# Data Provenance

## Synthetic demonstration data

Everything under `fixtures/` is fictional: agency names, contact labels, products, UPCs, lots, recall numbers, and package images. The recall payload declares `SYNTHETIC_DEMONSTRATION_DATA`; package art says “DEMONSTRATION PACKAGE — NOT FOR SALE.” Pillow generation is reproducible through `scripts/generate_fixture_images.py`; no third-party logos are used.

The three inventory rows intentionally provide one exact UPC+lot match, one same-UPC/missing-lot potential match, and one unrelated control.

## Uploaded source records

For an upload, the application records provider, operator-provided source URL, retrieval time, SHA-256, MIME, byte length, private media URI, and source limitation. Text/JSON content is preserved in the source record; original PDF bytes remain unchanged in the selected media store. Normalized extraction is stored separately as `Recall`; original data is never silently overwritten.

## openFDA import

The importer constructs only `https://api.fda.gov/food/enforcement.json` with an encoded recall-number query. It retains the returned record unmodified and stores the exact query URL and hash.

openFDA explicitly cautions that its data is not validated for clinical or production use and should not be used as a public-alert mechanism or as the official recall lifecycle. Operators must confirm the current FDA/USDA notice and organization policy.

## AI provenance

Audit records include selected mode, configured model, duration/outcome when available, and short source evidence—never hidden reasoning. Mock and replay results are not live calls. Package observations remain human-review signals regardless of confidence wording.

## Internal closure terminology

`INTERNAL_CLOSED` means the organization completed the recorded internal operational workflow. It does not assert regulator verification, official closure, product safety, or disposition authorization.
