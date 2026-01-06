import argparse
import torch
from transformers import AutoTokenizer, AutoModel
try:
    from onnxruntime.quantization import quantize_dynamic, QuantType
except Exception:
    quantize_dynamic = None
    QuantType = None

# Export a transformer encoder + mean-pooling to ONNX
class MeanPoolModel(torch.nn.Module):
    def __init__(self, base_model):
        super().__init__()
        self.base = base_model

    def forward(self, input_ids, attention_mask):
        outputs = self.base(input_ids=input_ids, attention_mask=attention_mask)
        last_hidden = outputs.last_hidden_state  # (batch, seq, dim)
        mask = attention_mask.unsqueeze(-1).to(last_hidden.dtype)
        summed = (last_hidden * mask).sum(1)
        counts = mask.sum(1).clamp(min=1)
        mean_pooled = summed / counts
        return mean_pooled


def export(model_name, output_path, opset=13):
    tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
    base = AutoModel.from_pretrained(model_name)
    model = MeanPoolModel(base)
    model.eval()

    # create dummy inputs
    inputs = tokenizer(["Hello world", "Dit is een test"], padding='longest', return_tensors='pt')
    input_ids = inputs['input_ids']
    attention_mask = inputs['attention_mask']

    # trace and export
    with torch.no_grad():
        torch.onnx.export(
            model,
            (input_ids, attention_mask),
            output_path,
            input_names=['input_ids', 'attention_mask'],
            output_names=['pooled'],
            dynamic_axes={
                'input_ids': {0: 'batch', 1: 'sequence'},
                'attention_mask': {0: 'batch', 1: 'sequence'},
                'pooled': {0: 'batch'}
            },
            opset_version=opset,
        )
    # Optionally quantize the exported model to reduce runtime size
    if quantize_dynamic is not None:
        quant_out = output_path.replace('.onnx', '-quant.onnx')
        try:
            quantize_dynamic(output_path, quant_out, weight_type=QuantType.QInt8)
            print(f'Quantized model written to {quant_out}')
            # replace output_path with quantized file for runtime use
            output_path = quant_out
        except Exception as e:
            print(f'Quantization failed: {e}; continuing with FP32 model')
    # Ensure a model-quant.onnx exists for the runtime Dockerfile to COPY.
    # If quantization didn't run or failed, copy the FP32 model to model-quant.onnx
    try:
        import os, shutil
        quant_path = output_path.replace('.onnx', '-quant.onnx')
        if not os.path.exists(quant_path):
            shutil.copyfile(output_path, quant_path)
            print(f'Created fallback quant file at {quant_path}')
    except Exception as e:
        print(f'Warning: could not create fallback quant model: {e}')
    # save tokenizer files next to the ONNX model so the runtime can load them with `tokenizers`
    import os
    out_dir = os.path.dirname(output_path) or '.'
    tok_dir = os.path.join(out_dir, 'tokenizer')
    tokenizer.save_pretrained(tok_dir)

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--model_name', default='sentence-transformers/all-MiniLM-L6-v2')
    p.add_argument('--output', dest='output', default='model.onnx')
    p.add_argument('--output_dir', dest='output_dir', default=None)
    args = p.parse_args()
    out = args.output
    if args.output_dir:
        out = args.output_dir.rstrip('/') + '/' + out
    print(f'Exporting {args.model_name} -> {out}')
    export(args.model_name, out)
