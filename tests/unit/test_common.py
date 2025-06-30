from unittest import IsolatedAsyncioTestCase, mock
from aigc import common
from aigc.models.db import MagicPointSubscription, SubscriptionType
from datetime import datetime


class TestUtilsFunctions(IsolatedAsyncioTestCase):

    async def test_query_valid_subscriptions(self):
        ses = mock.MagicMock()
        dt = datetime(2025, 1, 1)
        faketrail: MagicPointSubscription = MagicPointSubscription(
            id=1,
            uid=1,
            stype=SubscriptionType.trail,
            init=30,
            remains=30,
            ctime=dt,
            utime=dt,
        )
        fakesubscription: MagicPointSubscription = MagicPointSubscription(
            id=1,
            uid=1,
            stype=SubscriptionType.subscription,
            init=30,
            remains=30,
            ctime=dt,
            utime=dt,
        )
        ses.exec.return_value.all.return_value = [faketrail]

        # test have trail, return trail
        s = await common.query_valid_subscription(1, ses)
        self.assertEqual(s, faketrail)

        # test have subscription and trail, use subscription
        ses.exec.return_value.all.return_value = [faketrail, fakesubscription]
        s = await common.query_valid_subscription(1, ses)
        self.assertEqual(s, fakesubscription, "expect return subscription")

