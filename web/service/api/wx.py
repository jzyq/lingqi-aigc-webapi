from fastapi import APIRouter
from fastapi.responses import RedirectResponse
import rpcclient


router = APIRouter(prefix="/wx")


# @router.get("/login/callback")
# async def wechat_login_callback(
#     code: str,
#     state: str,
#     rdb: deps.Rdb,
#     db: Session = Depends(deps.get_db_session),
#     conf: config.Config = Depends(config.get_config),
#     wx: wechat.client.WxClient = Depends(deps.get_wxclient),
# ):

#     # Fetch use info
#     logger.info("wx login callback.")
#     try:
#         tk = await wx.require_access_token(code)
#         user_info = await wx.fetch_user_info(
#             openid=tk.openid, access_token=tk.access_token
#         )
#         logger.info(f"unionid {user_info.unionid}, nickname: {user_info.nickname}")
#     except wechat.CallError as e:
#         logger.error(f"fetch wx user info error, {e}")
#         raise HTTPException(status_code=500, detail=e.msg)

#     exists_wxuinfo = db.exec(
#         select(database.wechat.UserInfo).where(
#             database.wechat.UserInfo.unionid == user_info.unionid
#         )
#     ).one_or_none()

#     # If wx user already exists. just do login.
#     if exists_wxuinfo is not None:
#         logger.debug(f"already have user {exists_wxuinfo.unionid}")

#         user = db.get(database.user.User, exists_wxuinfo.uid)
#         assert user is not None and user.id is not None

#         # If already login and valid, use same one.
#         result = await sessions.find_session_by_uid(rdb, user.id)

#         if result is not None:
#             token, _ = result
#             logger.info(f"login with old token {token}")
#             return RedirectResponse(url=f"{state}?token={token}")

#         # If no login, create a new session.
#         token = await sessions.create_new_session(rdb, user.id, user.nickname)
#         logger.info(f"login with new token {token}")
#         return RedirectResponse(url=f"{state}?token={token}")

#     # No wx user, create a new user and associate to this wx user.
#     else:
#         logger.info(f"new wx user {user_info.unionid} register.")

#         # Create new user.
#         new_user = database.user.User(
#             username=f"wx_{user_info.unionid}",
#             nickname=user_info.nickname,
#             avatar=user_info.headimgurl,
#             wx_id=user_info.unionid,
#         )
#         db.add(new_user)
#         db.commit()
#         db.refresh(new_user)

#         # Associate user and wx user info then write to database.
#         assert new_user.id is not None

#         wx_record = database.wechat.UserInfo(
#             openid=user_info.openid,
#             uid=new_user.id,
#             avatar=user_info.headimgurl,
#             nickname=user_info.nickname,
#             unionid=user_info.unionid,
#         )
#         db.add(wx_record)
#         db.commit()

#         # Give a init point subscription.
#         dt = datetime.now()
#         init_point = conf.magic_points.trail_free_point
#         subscription = database.subscription.Subscription(
#             uid=new_user.id,
#             stype=database.subscription.Type.trail,
#             init=init_point,
#             remains=init_point,
#             ctime=dt,
#             utime=dt,
#         )
#         db.add(subscription)
#         db.commit()

#         token = await sessions.create_new_session(rdb, new_user.id, new_user.nickname)
#         logger.info(f"login with new token {token}")

#         # 重定向到前端并携带token
#         return RedirectResponse(url=f"{state}?token={token}")


# @router.post("/pay/callback")
# async def wechat_pay_callback(
#     request: Request,
#     wechatpay_timestamp: Annotated[str, Header()],
#     wechatpay_nonce: Annotated[str, Header()],
#     wechatpay_signature: Annotated[str, Header()],
#     db: Session = Depends(deps.get_db_session),
#     wx: wechat.client.WxClient = Depends(deps.get_wxclient),
#     conf: config.Config = Depends(config.get_config),
# ) -> Response:

#     body = await request.body()

#     # Verify if data come from wx server.
#     if not wx.verify(
#         wechatpay_timestamp, wechatpay_nonce, wechatpay_signature, body.decode()
#     ):
#         raise HTTPException(
#             status_code=400,
#             detail=json.dumps({"code": "FAIL", "message": "失败"}, ensure_ascii=False),
#         )

#     # Decrypt pay result.
#     req = models.payment.PayCallbackRequest.model_validate_json(body)
#     assert req.resource.algorithm == "AEAD_AES_256_GCM"
#     plaintext = wx.decrypt(
#         req.resource.ciphertext, req.resource.nonce, req.resource.associated_data
#     )
#     result = models.payment.PayCallbackResult.model_validate_json(plaintext)
#     logger.debug(result.model_dump_json())

#     recharage_order = db.exec(
#         select(database.pay.Recharge).where(
#             database.pay.Recharge.tradeid == result.out_trade_no
#         )
#     ).one()

#     assert result.amount.total == recharage_order.amount

#     # Update recharge order state.
#     recharage_order.transaction_id = result.transaction_id
#     recharage_order.success_time = common.dt.parse_datetime(result.success_time)
#     recharage_order.reason = result.trade_state_desc
#     if result.trade_state != "SUCCESS":
#         logger.warning(f"pay failed of trade {result.out_trade_no}")
#         recharage_order.pay_state = database.pay.State.failed
#     else:
#         logger.info(f"pay success of trade {result.out_trade_no}")
#         recharage_order.pay_state = database.pay.State.success

#         # TODO: update user subscription.
#         subplan: config.MagicPointSubscription | None = None
#         for p in conf.magic_points.subscriptions:
#             if recharage_order.amount == p.price:
#                 subplan = p
#                 break
#         assert subplan is not None

#         # Expire current subscription.
#         current_sub = db.exec(
#             select(database.subscription.Subscription)
#             .where(database.subscription.Subscription.uid == recharage_order.uid)
#             .where(database.subscription.Subscription.expired == False)
#             .where(
#                 database.subscription.Subscription.stype
#                 == database.subscription.Type.subscription
#             )
#         ).one_or_none()

#         if current_sub is not None:
#             current_sub.expired = True

#         # Set new subscription.
#         dt = datetime.now()
#         expires_in = dt.replace(
#             hour=0, minute=0, second=0, microsecond=0
#         ) + relativedelta(months=subplan.month)
#         newsub = database.subscription.Subscription(
#             uid=recharage_order.uid,
#             stype=database.subscription.Type.subscription,
#             init=subplan.points,
#             remains=subplan.points,
#             ctime=dt,
#             utime=dt,
#             expires_in=expires_in,
#         )
#         db.add(newsub)
#         logger.info(
#             f"uid {recharage_order.uid} new subscription, {subplan.price/100} for {subplan.month}, {subplan.points} each day."
#         )

#     db.commit()

#     return Response()


@router.get("/qrlogin")
async def qrcode_login() -> RedirectResponse:
    client = rpcclient.Client()
    url = await client.wechat.generate_login_qrcode_url()
    return RedirectResponse(url=url)
