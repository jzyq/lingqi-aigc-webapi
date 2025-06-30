from unittest import mock, IsolatedAsyncioTestCase
from aigc.api.wx import wechat_login_callback
from fastapi.responses import RedirectResponse
from aigc.wx.client import WxClient
from aigc.wx.models import UserInfo, UserSex
from aigc.models.db import User, MagicPointSubscription, SubscriptionType
import aigc.api.wx
from datetime import datetime


class TestQrLoginAPI(IsolatedAsyncioTestCase):

    @mock.patch.object(aigc.api.wx, "datetime", autospec=True)
    @mock.patch.object(aigc.api.wx.sessions, "create_new_session", autospec=True)
    async def test_wx_callback_with_new_user(self, fakeses: mock.MagicMock, fake_datetime: mock.MagicMock) -> None:

        fakecode: str = "100"
        fakestate: str = "state"

        fakedb = mock.MagicMock()
        fakedb.exec.return_value.one_or_none.return_value = None

        def fake_refresh(user: User) -> None:
            user.id = 1
        fakedb.refresh.side_effect = fake_refresh

        fakerdb = mock.AsyncMock()

        fakewx = mock.AsyncMock(spec=WxClient)
        fakewx.fetch_user_info.return_value = UserInfo(
            openid="123", nickname="abc", sex=UserSex.male,
            province="", city="", country="", headimgurl="", privilege=[], unionid="id")

        fakeconf = mock.AsyncMock()
        fakeconf.magic_points.trail_free_point = 100

        fakedt = datetime(2000, 1, 1)
        fake_datetime.now.return_value = fakedt

        fakeses.return_value = "token"

        resp = await wechat_login_callback(fakecode, fakestate, fakedb, fakerdb, fakewx, fakeconf)

        self.assertIsInstance(resp, RedirectResponse)

        s = MagicPointSubscription(uid=1, stype=SubscriptionType.subscription,
                               init=100, remains=100, ctime=fakedt, utime=fakedt)
        fakedb.add.assert_called_with(s)
