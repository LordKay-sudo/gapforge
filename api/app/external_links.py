"""Federated deep links for genes (Open Targets / Ensembl / UniProt)."""
from __future__ import annotations

from app.models.schemas import ExternalLink, GeneExternalLinksResponse


def ensembl_gene_url(gene_id: str) -> str:
    return f"https://www.ensembl.org/Homo_sapiens/Gene/Summary?g={gene_id}"


def open_targets_url(gene_id: str) -> str:
    return f"https://platform.opentargets.org/target/{gene_id}"


def uniprot_url(protein_id: str) -> str:
    return f"https://www.uniprot.org/uniprotkb/{protein_id}"


def build_gene_external_links(
    gene_id: str,
    symbol: str,
    uniprot_ids: list[str],
) -> GeneExternalLinksResponse:
    links: list[ExternalLink] = [
        ExternalLink(
            label="Ensembl",
            provider="ensembl",
            url=ensembl_gene_url(gene_id),
        ),
        ExternalLink(
            label="Open Targets",
            provider="opentargets",
            url=open_targets_url(gene_id),
        ),
    ]
    for pid in uniprot_ids[:3]:
        links.append(
            ExternalLink(
                label=f"UniProt ({pid})",
                provider="uniprot",
                url=uniprot_url(pid),
            )
        )
    return GeneExternalLinksResponse(gene_id=gene_id, symbol=symbol, links=links)
