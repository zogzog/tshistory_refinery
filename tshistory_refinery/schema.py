from pathlib import Path

from sqlhelp import sqlfile

from rework.schema import init as rework_init
from rework_ui.schema import init as rework_ui_init
from tshistory.schema import tsschema
from tshistory_formula.schema import formula_schema


CACHE_POLICY = Path(__file__).parent / 'schema.sql'


def init(engine, namespace='tsh', rework=True, drop=False):
    tsschema(namespace).create(engine, reset=drop)
    tsschema(f'{namespace}-upstream').create(engine)
    formula_schema(namespace).create(engine)

    if rework:
        rework_init(engine, drop=drop)
        rework_ui_init(engine)

    with engine.begin() as cn:
        cn.execute(sqlfile(CACHE_POLICY, ns=namespace))
    tsschema(f'{namespace}-cache').create(engine)
