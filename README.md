# emStanzaDep
Stanza tools adapted to the xtsv framework.

## Requirements
- Python >= 3.6
- make

## Installation
- Install git-lfs
- `git-lfs install`
- Clone the repository: `git clone https://github.com/ELTE-DH/emstanza`
- `make build`
- `pip install dist/*.whl`

## Usage
- Same as any other module using the xtsv framework - either as part of the emtsv framework or as separate module.

### Configurations

- `tok`: Tokenizes text. Requires no fields and generates `form`, `wsafter` fields
- `tok-pos`: Tokenizes and POS-tags text. Requires no fields and generates `form`, `wsafter`, `feats`, `upostag`, `xpostag` fields
- `tok-lem`: Tokenizes, POS-tags, and lemmatizes text. Requires no fields and generates `form`, `wsafter`, `feats`, `upostag`, `xpostag`, `lemma` fields
- `tok-parse`: Tokenizes, POS-tags, lemmatizes and dependency parses text. Requires no fields and generates `form`, `wsafter`, `feats`, `upostag`, `xpostag`, `lemma`, `id`, `head`, `deprel` fields
- `parse`: Dependency parses text. Requires `form`, `lemma`, `upostag`, `feats` and generates `id`, `deprel`, `head` fields.

## License
This xtsv wrapper is licensed under the LGPL 3.0 license. The model and the included .pt files have their own licenses.



