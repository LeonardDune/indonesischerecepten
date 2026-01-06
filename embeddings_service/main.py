from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import os
import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer

app = FastAPI()

MODEL_PATH = os.getenv("ONNX_MODEL_PATH", "./model-quant.onnx")
TOKENIZER_PATH = os.getenv("TOKENIZER_PATH", "./tokenizer/tokenizer.json")

class EmbedRequest(BaseModel):
    texts: List[str]

class EmbedResponse(BaseModel):
    embeddings: List[List[float]]

# load tokenizer (fast/tokenizers) and onnx session once
try:
    tokenizer = Tokenizer.from_file(TOKENIZER_PATH)
except Exception as e:
    raise RuntimeError(f'Failed to load tokenizer at {TOKENIZER_PATH}: {e}')
# create ONNX Runtime session with conservative threading and memory options to reduce RAM usage
try:
    sess_options = ort.SessionOptions()
    # reduce thread usage
    try:
        sess_options.intra_op_num_threads = 1
        sess_options.inter_op_num_threads = 1
    except Exception:
        pass
    # favor sequential execution and reduce arena/mempattern allocations
    try:
        from onnxruntime import ExecutionMode, GraphOptimizationLevel
        sess_options.execution_mode = ExecutionMode.ORT_SEQUENTIAL
        sess_options.graph_optimization_level = GraphOptimizationLevel.ORT_ENABLE_BASIC
    except Exception:
        pass
    try:
        sess_options.enable_mem_pattern = False
        sess_options.enable_cpu_mem_arena = False
    except Exception:
        pass

    sess = ort.InferenceSession(MODEL_PATH, sess_options=sess_options, providers=['CPUExecutionProvider'])
except Exception as e:
    raise RuntimeError(f'Failed to load ONNX model at {MODEL_PATH}: {e}')

def run_onnx(texts: List[str]):
    # Tokenize using the fast `tokenizers` Tokenizer to avoid loading `transformers` at runtime
    encs = [tokenizer.encode(t) for t in texts]
    ids_list = [e.ids for e in encs]
    mask_list = [e.attention_mask for e in encs]
    max_len = max(len(x) for x in ids_list)
    input_ids = np.zeros((len(ids_list), max_len), dtype='int64')
    attention_mask = np.zeros((len(ids_list), max_len), dtype='int64')
    for i, (ids, mask) in enumerate(zip(ids_list, mask_list)):
        input_ids[i, :len(ids)] = ids
        attention_mask[i, :len(mask)] = mask
    ort_inputs = {
        'input_ids': input_ids.astype('int64'),
        'attention_mask': attention_mask.astype('int64')
    }
    outs = sess.run(None, ort_inputs)
    # outs[0] is pooled embeddings
    return [o.tolist() for o in outs[0]]

@app.post("/embed", response_model=EmbedResponse)
async def embed(req: EmbedRequest):
    try:
        embs = run_onnx(req.texts)
        return {"embeddings": embs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
