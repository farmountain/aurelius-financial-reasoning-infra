"""Alembic version template."""
# revision identifiers, used by Alembic.
revision = ${repr(up)}
down_revision = ${repr(down)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
