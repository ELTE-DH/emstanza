# emStanzaDep
Stanza dependency parser fitted to the xtsv framework.

## Requirements
- Python >= 3.6
- make

## Installation
- Install git-lfs
- `git-lfs install`
- Clone the repository: `git clone https://github.com/ELTE-DH/emstanzadep`
- `make build`
- `pip install dist/*.whl`

## Usage
- Same as any other module using the xtsv framework - either as part of the emtsv framework or as separate module.
- The required fields are: `'form', 'lemma', 'upostag', 'feats'`, outputs `'id', 'deprel', 'head'`
- The parameter `--naming_convention` chooses between two UDv1* (experimental, `magyarlanc`) and UDv2 convention (`stanza`). By default, it uses UDv2.

## License
This xtsv wrapper is licensed under the LGPL 3.0 license. The model and the included .pt file have their own licenses.



