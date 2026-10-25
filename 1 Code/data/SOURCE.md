# Local dataset provenance

Dataset: Amazon Review Data (2018), Gift Cards, 5-core review subset.
Main source: https://nijianmo.github.io/amazon/index.html
Official lab mirror: https://mcauleylab.ucsd.edu/public_datasets/data/amazon_v2/
Downloaded file: https://mcauleylab.ucsd.edu/public_datasets/data/amazon_v2/categoryFilesSmall/Gift_Cards_5.json.gz
Verified/downloaded: 2026-10-22.

The source page lists 2,972 reviews in the Gift Cards 5-core subset. The complete
Gift Cards category has 147,194 reviews. Both original archives are included.
5-core is a dense subset with repeated user/product activity, so it is not a
representative sample of all Amazon reviews. Do not confuse its row count with
the full category. The dataset is historical; it is not a live product feed.

Local file: `Gift_Cards_5.json.gz` (177,783 compressed bytes).
SHA-256: `e8b25bb899869108e46417a7f1cf741b6ecae83336ed6500e4ecd87e046ed55e`.
Format: gzip-compressed JSON Lines, one review object per line.

Full category file: `Gift_Cards.json.gz` (11,064,635 compressed bytes).
Download: https://mcauleylab.ucsd.edu/public_datasets/data/amazon_v2/categoryFiles/Gift_Cards.json.gz
Verified local row count: 147,194.
SHA-256: `c8e18cd3f0baf97bdce2887ec6644d58506736610131019801a0a27dbb96e77b`.
The starter uses the 5-core file for Phase1. Kekelani's Phase2 workspace points
to this full archive for the required larger sample.

Original archive is preserved. The script derives cleaned CSVs reproducibly.
Original jmcauley.ucsd.edu download had an expired certificate at setup time;
the lab's mcauleylab.ucsd.edu mirror supplied the file over valid HTTPS.

Suggested citation:
Jianmo Ni, Jiacheng Li, and Julian McAuley (2019). Justifying Recommendations
using Distantly-Labeled Reviews and Fine-Grained Aspects. EMNLP-IJCNLP.
https://aclanthology.org/D19-1018/

Follow the source's research-use request and cite it in the submitted report.
