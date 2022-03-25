import os

import pytest
from cryptoadvance.specterext.ampissuer.amp import Amp


@pytest.mark.skip("dependent on credentials")
def test_Amp(bitcoin_regtest):
    token = os.environ["AMP_AUTH"]
    amp = Amp("https://amp-test.blockstream.com/api/",token,"s")
    assert amp.assets == {}
    #print(amp.obtain_token("someuser","somepassword"))
    # The testarea for amp:
    # amp.some_method()
    assert False
