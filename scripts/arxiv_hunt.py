import arxiv
import json

search = arxiv.Search(
    query='Neem "spectral signature"',
    max_results=5,
    sort_by=arxiv.SortCriterion.Relevance
)

results = []
for r in search.results():
    results.append({
        "title": r.title,
        "pdf": r.pdf_url
    })

print(json.dumps(results))
