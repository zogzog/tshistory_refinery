from psyl import lisp

from tshistory.util import tx
from tshistory.tsio import timeseries as basets
from tshistory_xl.tsio import timeseries as xlts

from tshistory_refinery import cache


class timeseries(xlts):

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.cache = basets(namespace='{}-cache'.format(self.namespace))

    @tx
    def get(self, cn, name, nocache=False, **kw):
        if self.type(cn, name) != 'formula':
            return super().get(cn, name, **kw)

        if not nocache:
            ready = cache.ready(cn, name, namespace=self.namespace)
            if ready is not None and ready:
                return self.cache.get(cn, name, **kw)

        return super().get(cn, name, **kw)

    @tx
    def insertion_dates(self, cn, name,
                        from_insertion_date=None,
                        to_insertion_date=None,
                        nocache=False,
                        **kw):
        if self.type(cn, name) != 'formula':
            return super().insertion_dates(
                cn, name,
                from_insertion_date=from_insertion_date,
                to_insertion_date=to_insertion_date,
                **kw
            )


        if not nocache:
            ready = cache.ready(cn, name, namespace=self.namespace)
            if ready is not None and ready:
                return self.cache.insertion_dates(
                    cn, name,
                    from_insertion_date=from_insertion_date,
                    to_insertion_date=to_insertion_date,
                    **kw
                )

        return super().insertion_dates(
            cn, name,
            from_insertion_date=from_insertion_date,
            to_insertion_date=to_insertion_date,
            **kw
        )

    @tx
    def history(self, cn, name,
                nocache=False,
                **kw):
        if self.type(cn, name) != 'formula':
            return super().history(
                cn, name, **kw
            )

        if not nocache:
            ready = cache.ready(cn, name, namespace=self.namespace)
            if ready is not None and ready:
                return self.cache.history(cn, name, **kw)

        return super().history(
            cn, name, **kw
        )

    @tx
    def rename(self, cn, oldname, newname):
        if self.type(cn, oldname) == 'formula':
            ready = cache.ready(cn, oldname, namespace=self.namespace)
            if ready is not None:
                self.cache.rename(cn, oldname, newname)

        return super().rename(cn, oldname, newname)

    @tx
    def delete(self, cn, name):
        if self.type(cn, name) == 'formula':
            ready = cache.ready(cn, name, namespace=self.namespace)
            if ready is not None:
                self.cache.delete(cn, name)

        return super().delete(cn, name)

    @tx
    def invalidate_cache(self, cn, name):
        ready = cache.ready(cn, name, namespace=self.namespace)
        if ready is not None:
            cache.invalidate(cn, name, namespace=self.namespace)
            self.cache.delete(cn, name)

    @tx
    def cacheable_formulas(self, cn):
        formulas = dict(
            cn.execute(
                f'select name, text '
                f'from "{self.namespace}".formula'
            ).fetchall()
        )
        primaries = {
            name
            for name, in cn.execute(
                    f'select seriesname from "{self.namespace}".registry'
            ).fetchall()
        }

        def only_local(formula):
            tree = self._expanded_formula(cn, formula)
            for name in self.find_series(cn, tree):
                if name in formulas or name in primaries:
                    continue
                return False
            return True

        return [
            name
            for name, text in formulas.items()
            if only_local(text)
        ]

    @tx
    def register_formula(self, cn, name, formula, reject_unknown=True):
        prevch = self.content_hash(cn, name)
        super().register_formula(
            cn, name, formula,
            reject_unknown=reject_unknown
        )
        if prevch != self.content_hash(cn, name):
            self.invalidate_cache(cn, name)
            for name in self.dependants(cn, name):
                self.invalidate_cache(cn, name)
