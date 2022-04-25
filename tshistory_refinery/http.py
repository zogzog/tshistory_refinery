from flask_restx import (
    inputs,
    Resource,
    reqparse
)

from tshistory.http.util import onerror
from tshistory.http.client import unwraperror
from tshistory_xl.http import (
    xl_httpapi,
    XLClient
)

from tshistory_refinery import cache


cp = reqparse.RequestParser()
cp.add_argument(
    'name',
    type=str,
    required=True,
    help='cache policy name'
)

newcp = cp.copy()
newcp.add_argument(
    'initial_revdate',
    type=str,
    required=True,
    help='initial revision date'
)
newcp.add_argument(
    'from_date',
    type=str,
    required=True,
    help='initial value date'
)
newcp.add_argument(
    'look_before',
    type=str,
    required=True,
    help='date expression to provide the refresh horizon on the left'
)
newcp.add_argument(
    'look_after',
    type=str,
    required=True,
    help='date expression to provide the refresh horizon on the right'
)
newcp.add_argument(
    'revdate_rule',
    type=str,
    required=True,
    help='cron rule for the revision date'
)
newcp.add_argument(
    'schedule_rule',
    type=str,
    required=True,
    help='cron rule to schedule the refresher'
)



class refinery_httpapi(xl_httpapi):
    __slots__ = 'tsa', 'bp', 'api', 'nss', 'nsg'

    def routes(self):
        super().routes()

        tsa = self.tsa
        api = self.api
        nsc = self.nsc = self.api.namespace(
            'cache',
            description='Formula Cache Operations'
        )

        @nsc.route('/policy')
        class formula_cache(Resource):

            @api.expect(newcp)
            @onerror
            def put(self):
                args = newcp.parse_args()
                try:
                    tsa.new_cache_policy(
                        args.name,
                        args.initial_revdate,
                        args.from_date,
                        args.look_before,
                        args.look_after,
                        args.revdate_rule,
                        args.schedule_rule
                    )
                except Exception as e:
                    api.abort(409, str(e))

                return '', 204


            @api.expect(newcp)
            @onerror
            def patch(self):
                args = newcp.parse_args()
                try:
                    tsa.edit_cache_policy(
                        args.name,
                        args.initial_revdate,
                        args.from_date,
                        args.look_before,
                        args.look_after,
                        args.revdate_rule,
                        args.schedule_rule
                    )
                except Exception as e:
                    api.abort(409, str(e))

                return '', 204


class RefineryClient(XLClient):

    def __repr__(self):
        return f"refinery-http-client(uri='{self.uri}')"

    @unwraperror
    def new_cache_policy(
            self,
            name,
            initial_revdate,
            from_date,
            look_before,
            look_after,
            revdate_rule,
            schedule_rule):

        res = self.session.put(f'{self.uri}/cache/policy', data={
            'name': name,
            'initial_revdate': initial_revdate,
            'from_date': from_date,
            'look_before': look_before,
            'look_after': look_after,
            'revdate_rule': revdate_rule,
            'schedule_rule': schedule_rule
        })

        if res.status_code == 409:
            raise ValueError(res.json()['message'])

        if res.status_code == 204:
            return

        return res

    @unwraperror
    def edit_cache_policy(
            self,
            name,
            initial_revdate,
            from_date,
            look_before,
            look_after,
            revdate_rule,
            schedule_rule):

        res = self.session.patch(f'{self.uri}/cache/policy', data={
            'name': name,
            'initial_revdate': initial_revdate,
            'from_date': from_date,
            'look_before': look_before,
            'look_after': look_after,
            'revdate_rule': revdate_rule,
            'schedule_rule': schedule_rule
        })

        if res.status_code == 409:
            raise ValueError(res.json()['message'])

        if res.status_code == 204:
            return

        return res
