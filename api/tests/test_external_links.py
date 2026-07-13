from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@patch("app.routers.genes.get_session")
def test_get_gene_external_links(mock_session):
    class FakeSession:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def run(self, query, **params):
            class Result:
                def single(self):
                    return {"id": "ENSG00000012048", "symbol": "BRCA1"}

                def __iter__(self):
                    if "Protein" in query:
                        return iter([{"id": "P38398"}])
                    return iter([])

            return Result()

    mock_session.return_value = FakeSession()

    r = client.get("/api/v1/genes/ENSG00000012048/external-links")
    assert r.status_code == 200
    body = r.json()
    assert body["symbol"] == "BRCA1"
    urls = {link["provider"]: link["url"] for link in body["links"]}
    assert "ensembl.org" in urls["ensembl"]
    assert "opentargets.org" in urls["opentargets"]
    assert "uniprot.org" in urls["uniprot"]
