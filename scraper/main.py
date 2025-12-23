import argparse
import json
import sys
import os
import requests
from scraper.discovery import Discovery
from scraper.extract import Extractor
from scraper.detect import Detector
from scraper.consolidate import Consolidator
from scraper.rdf_writer import RDFWriter

def cmd_discover(args):
    """Run discovery phase."""
    print("Starting discovery phase...")
    d = Discovery()
    
    if args.scope:
        start_paths = args.scope
    else:
        # Default roots from discovery default
        start_paths = ["/indonesian", "/thailand", "/china", "/filipijnen", "/korea", "/overige-gerechten"]
        
    recipe_urls = d.crawl(start_paths=start_paths)
    
    # Save to file
    output_file = args.output or "recipe_urls.json"
    with open(output_file, 'w') as f:
        json.dump(list(recipe_urls), f, indent=2)
    
    print(f"Discovery finished. Saved {len(recipe_urls)} URLs to {output_file}")

def cmd_extract(args):
    """Run extraction on a single URL for testing."""
    url = args.url
    print(f"Extracting {url}...")
    
    headers = {"User-Agent": "ResearchBot/1.0"}
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    
    e = Extractor()
    data = e.parse_html(r.text, url=url)
    
    print(json.dumps(data, indent=2, ensure_ascii=False))

def cmd_run(args):
    """Run full pipeline."""
    # Phase 1: Discovery
    d = Discovery()
    
    recipe_urls = []
    recipes_data = []

    if args.load_raw:
        print(f"Loading raw extraction data from {args.load_raw}...")
        with open(args.load_raw, 'r') as f:
            recipes_data = json.load(f)
        print(f"Loaded {len(recipes_data)} recipes.")
    else:
        # Check if a specific scope was provided
        if args.scope:
            # Heuristic: if first scope looks like a specific recipe, skip crawl
            if len(args.scope) == 1 and d.is_recipe_url(args.scope[0]):
                print(f"Scope is a single recipe: {args.scope[0]}")
                recipe_urls = [args.scope[0]]
            else:
                recipe_urls = d.crawl(start_paths=args.scope, limit=args.limit)
        else:
            # Default roots
            start_paths = ["/indonesian", "/thailand", "/china", "/filipijnen", "/korea", "/overige-gerechten"]
            recipe_urls = d.crawl(start_paths=start_paths, limit=args.limit)
            
        print(f"Found {len(recipe_urls)} recipes.")
        
        print("\n=== Phase 2: Extraction ===")
        extractor = Extractor()
        detector = Detector()
        
        headers = {"User-Agent": "ResearchBot/1.0"}
        
        for i, url in enumerate(recipe_urls):
            print(f"[{i+1}/{len(recipe_urls)}] Processing {url}...")
            try:
                r = requests.get(url, headers=headers)
                r.raise_for_status()
                data = extractor.parse_html(r.text, url=url)
                
                # Phase 3: Detection (Per recipe)
                data["detected"] = detector.detect(data)
                
                recipes_data.append(data)
            except Exception as e:
                print(f"Failed to process {url}: {e}")
            
    # Phase 6: Save Raw (Optional)
    if args.save_raw:
        with open(args.save_raw, 'w') as f:
            json.dump(recipes_data, f, indent=2, ensure_ascii=False)
        print(f"Raw extraction data saved to {args.save_raw}")

    # Phase 4: Consolidation
    # Lower threshold if running on a small scope for testing
    min_freq = 1 if args.scope else 2
    consolidator = Consolidator(min_frequency=min_freq)
    enriched_recipes, categories = consolidator.process(recipes_data)
    
    # Phase 5: RDF Generation
    writer = RDFWriter()
    g = writer.generate_graph(enriched_recipes, categories)
    
    output_ttl = args.output or "knowledge_graph.ttl"
    g.serialize(destination=output_ttl, format="turtle")
    print(f"Knowledge graph saved to {output_ttl}")

def main():
    parser = argparse.ArgumentParser(description="Kokkieblanda Knowledge Graph Scraper")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Discovery command
    parser_discover = subparsers.add_parser("discover", help="Discover recipe URLs")
    parser_discover.add_argument("--scope", nargs='+', help="Start paths (e.g. /indonesian)", default=None)
    parser_discover.add_argument("--output", help="Output JSON file", default="recipe_urls.json")
    parser_discover.set_defaults(func=cmd_discover)

    # Extract command
    parser_extract = subparsers.add_parser("extract", help="Extract single recipe")
    parser_extract.add_argument("url", help="URL to extract")
    parser_extract.set_defaults(func=cmd_extract)
    
    # Run full command
    parser_run = subparsers.add_parser('run', help='Run full pipeline')
    parser_run.add_argument('--scope', nargs='+', help='Target scopes (e.g. /indonesian /china)')
    parser_run.add_argument('--limit', type=int, help='Limit number of recipes')
    parser_run.add_argument('--output', help='Output TTL file')
    parser_run.add_argument('--save-raw', help='Save extraction results to JSON')
    parser_run.add_argument('--load-raw', help='Load extraction results from JSON')
    parser_run.set_defaults(func=cmd_run)
    
    args = parser.parse_args()
    
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
