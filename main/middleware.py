# class MyAuthMiddleware:
#     """
#     Custom middleware (insecure) that takes user IDs from the query string.
#     """
#
#     def __init__(self, app):
#         # Store the ASGI application we were passed
#         self.app = app
#
#     async def __call__(self, scope, receive, send):
#         # Look up user from query string (you should also do things like
#         # checking if it is a valid user ID, or if scope["user"] is already
#         # populated).
#         print(scope["query_string"])
#         # scope['user'] = await get_user(int(scope["query_string"]))
#
#         return await self.app(scope, receive, send)
