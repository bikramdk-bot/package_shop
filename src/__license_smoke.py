from license_manager import ensure_default_license, get_current_expiry, generate_token, apply_token, ensure_token_db, get_shop_id

ensure_token_db()
info0 = ensure_default_license()
print('default expiry', info0.expiry)

shop = get_shop_id()
print('shop', shop)

tok = generate_token(shop, 1)
print('token', tok)

ok, msg, info1 = apply_token(tok)
print('apply1', ok, msg, getattr(info1, 'expiry', None))

ok2, msg2, info2 = apply_token(tok)
print('apply2', ok2, msg2, getattr(info2, 'expiry', None))
