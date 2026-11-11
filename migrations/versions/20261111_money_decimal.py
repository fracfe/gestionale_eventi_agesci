"""Conserva i centesimi di importi e quote.

Revision ID: money_decimal_20261111
Revises: d324e2482509
"""
from alembic import op
import sqlalchemy as sa

revision = "money_decimal_20261111"
down_revision = "d324e2482509"
branch_labels = None
depends_on = None


def upgrade():
    for table, columns in (("eventi", ("quota_acconto", "quota_saldo")),
                           ("transazioni", ("importo",))):
        with op.batch_alter_table(table) as batch:
            for column in columns:
                batch.alter_column(column, existing_type=sa.Integer(),
                                   type_=sa.Numeric(14, 2), existing_nullable=False)


def downgrade():
    # Tornare a Integer eliminerebbe i centesimi. Recuperare il backup completo
    # precedente alla migrazione, insieme all'immagine corrispondente.
    raise RuntimeError("Downgrade distruttivo bloccato: ripristinare il backup pre-migrazione.")
