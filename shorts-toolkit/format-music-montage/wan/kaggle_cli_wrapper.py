# Kaggle CLI wrapper: the network proxy injects the real token into the Authorization header,
# but token introspection sends the token in the request body, so skip introspection.
import sys, os, io, contextlib
os.environ.setdefault("KAGGLE_API_TOKEN", "KGAT_proxyinjected0000000000000000")
with contextlib.redirect_stdout(io.StringIO()):
    import kaggle
from kaggle.api.kaggle_api_extended import KaggleApi
KaggleApi._introspect_token = lambda self, tok: "alperkdl"
kaggle.api.authenticate()
from kaggle.cli import main
sys.exit(main())
