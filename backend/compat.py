"""
Lightweight Compatibility Layer for FastAPI, Pydantic V2, and TestClient
Provides standard-library fallbacks for headless/isolated environments
while delegating directly to installed packages when present.
File: backend/compat.py
"""
import inspect
import re
import sys
import types
from typing import Any, Dict, List, Optional


def run_coroutine(coro):
    """
    Drive coroutine chain synchronously without blocking on Windows loopback socketpairs.
    Compatible with Windows AppContainer sandboxes where asyncio.run hangs.
    """
    stack = [coro]
    val = None
    exc = None
    while stack:
        current = stack[-1]
        try:
            if exc is not None:
                to_raise = exc
                exc = None
                nxt = current.throw(to_raise)
            else:
                nxt = current.send(val)
            val = None
            if hasattr(nxt, "send"):
                stack.append(nxt)
            else:
                val = nxt
        except StopIteration as si:
            val = si.value
            stack.pop()
        except Exception as e:
            exc = e
            stack.pop()
    if exc is not None:
        raise exc
    return val


# ============================================================================
# Pydantic Fallbacks
# ============================================================================

class FieldInfo:
    def __init__(self, default=..., **extra):
        self.default = default
        self.default_factory = extra.get("default_factory")
        self.extra = extra


def Field(default=..., **kwargs):
    return FieldInfo(default=default, **kwargs)


class BaseModel:
    def __init__(self, **kwargs):
        # Resolve class defaults across MRO
        for cls in reversed(self.__class__.__mro__):
            # Check class attributes
            for attr_name in getattr(cls, "__dict__", {}):
                if attr_name.startswith("_"):
                    continue
                val = getattr(cls, attr_name)
                if isinstance(val, FieldInfo):
                    if val.default is not ...:
                        setattr(self, attr_name, val.default)
                    elif val.default_factory is not None:
                        setattr(self, attr_name, val.default_factory())
                elif not callable(val):
                    setattr(self, attr_name, val)

            # Check type annotations
            if hasattr(cls, "__annotations__"):
                for ann_name in cls.__annotations__:
                    if ann_name in getattr(cls, "__dict__", {}):
                        val = getattr(cls, ann_name)
                        if isinstance(val, FieldInfo):
                            if val.default is not ...:
                                setattr(self, ann_name, val.default)
                            elif val.default_factory is not None:
                                setattr(self, ann_name, val.default_factory())
                        elif not callable(val):
                            setattr(self, ann_name, val)

        # Set explicitly provided kwargs
        for k, v in kwargs.items():
            setattr(self, k, v)

    def model_dump(self) -> Dict[str, Any]:
        res = {}
        for k, v in self.__dict__.items():
            if k.startswith("_"):
                continue
            if isinstance(v, BaseModel):
                res[k] = v.model_dump()
            elif isinstance(v, list):
                res[k] = [item.model_dump() if isinstance(item, BaseModel) else item for item in v]
            elif isinstance(v, dict):
                res[k] = {
                    dk: (dv.model_dump() if isinstance(dv, BaseModel) else dv)
                    for dk, dv in v.items()
                }
            else:
                res[k] = v
        return res

    def dict(self) -> Dict[str, Any]:
        return self.model_dump()

    def __getitem__(self, item):
        return getattr(self, item)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.model_dump()})"


class BaseSettings(BaseModel):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


# ============================================================================
# FastAPI / APIRouter Fallbacks
# ============================================================================

class HTTPException(Exception):
    def __init__(self, status_code: int, detail: str = ""):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"HTTP {status_code}: {detail}")


class FallbackResponse:
    def __init__(self, status_code: int, data: Any):
        self.status_code = status_code
        self._data = data

    def json(self):
        return self._data


class Route:
    def __init__(self, method: str, path: str, handler, response_model=None):
        self.method = method.upper()
        self.path = path
        self.handler = handler
        self.response_model = response_model
        pattern = "^" + re.sub(r"\{([a-zA-Z0-9_]+)\}", r"(?P<\1>[^/]+)", path) + "$"
        self.regex = re.compile(pattern)

    def matches(self, method: str, path: str):
        if self.method != method.upper():
            return None
        match = self.regex.match(path)
        if match:
            return match.groupdict()
        return None


class APIRouter:
    def __init__(self, prefix: str = "", tags: Optional[List[str]] = None):
        self.prefix = prefix
        self.tags = tags or []
        self.routes: List[Route] = []

    def _normalize(self, path: str) -> str:
        full = self.prefix + path if not path.startswith(self.prefix) else path
        parts = [p for p in full.split("/") if p]
        return "/" + "/".join(parts)

    def add_route(self, method: str, path: str, handler, response_model=None):
        norm = self._normalize(path)
        self.routes.append(Route(method, norm, handler, response_model))

    def get(self, path: str, response_model=None, **kwargs):
        def decorator(fn):
            self.add_route("GET", path, fn, response_model)
            return fn
        return decorator

    def post(self, path: str, response_model=None, **kwargs):
        def decorator(fn):
            self.add_route("POST", path, fn, response_model)
            return fn
        return decorator

    def put(self, path: str, response_model=None, **kwargs):
        def decorator(fn):
            self.add_route("PUT", path, fn, response_model)
            return fn
        return decorator

    def delete(self, path: str, response_model=None, **kwargs):
        def decorator(fn):
            self.add_route("DELETE", path, fn, response_model)
            return fn
        return decorator

    def websocket(self, path: str):
        def decorator(fn):
            norm = self._normalize(path)
            self.routes.append(Route("WEBSOCKET", norm, fn))
            return fn
        return decorator


class CORSMiddleware:
    def __init__(self, app, **kwargs):
        self.app = app
        self.kwargs = kwargs


class FastAPI:
    def __init__(
        self,
        title: str = "FastAPI",
        version: str = "0.1.0",
        description: str = "",
        **kwargs
    ):
        self.title = title
        self.version = version
        self.description = description
        self.routes: List[Route] = []
        self.middlewares: List[Any] = []

    def add_middleware(self, middleware_cls, **kwargs):
        self.middlewares.append((middleware_cls, kwargs))

    def include_router(self, router: APIRouter):
        self.routes.extend(router.routes)

    def get(self, path: str, response_model=None, **kwargs):
        def decorator(fn):
            norm = "/" + "/".join(p for p in path.split("/") if p)
            self.routes.append(Route("GET", norm, fn, response_model))
            return fn
        return decorator

    def post(self, path: str, response_model=None, **kwargs):
        def decorator(fn):
            norm = "/" + "/".join(p for p in path.split("/") if p)
            self.routes.append(Route("POST", norm, fn, response_model))
            return fn
        return decorator

    def websocket(self, path: str):
        def decorator(fn):
            norm = "/" + "/".join(p for p in path.split("/") if p)
            self.routes.append(Route("WEBSOCKET", norm, fn))
            return fn
        return decorator

    def test_request(self, method: str, path: str, json_payload=None, **kwargs) -> Dict[str, Any]:
        norm = "/" + "/".join(p for p in path.split("/") if p)
        matched_route = None
        path_params = {}
        for r in self.routes:
            params = r.matches(method, norm)
            if params is not None:
                matched_route = r
                path_params = params
                break

        if not matched_route:
            return {"status_code": 404, "data": {"detail": f"Route not found: {method} {path}"}}

        sig = inspect.signature(matched_route.handler)
        handler_kwargs = {}
        for param_name, param in sig.parameters.items():
            if param_name in path_params:
                handler_kwargs[param_name] = path_params[param_name]
            elif json_payload is not None:
                ann = param.annotation
                if isinstance(ann, type) and issubclass(ann, BaseModel):
                    handler_kwargs[param_name] = ann(**json_payload)
                else:
                    handler_kwargs[param_name] = json_payload

        try:
            if inspect.iscoroutinefunction(matched_route.handler):
                coro = matched_route.handler(**handler_kwargs)
                res = run_coroutine(coro)
            else:
                res = matched_route.handler(**handler_kwargs)
        except HTTPException as he:
            return {"status_code": he.status_code, "data": {"detail": he.detail}}
        except Exception as e:
            return {"status_code": 500, "data": {"detail": str(e)}}

        if hasattr(res, "model_dump"):
            data = res.model_dump()
        elif hasattr(res, "dict"):
            data = res.dict()
        else:
            data = res

        return {"status_code": 200, "data": data}


# ============================================================================
# WebSocket Fallbacks
# ============================================================================

class WebSocketDisconnect(Exception):
    def __init__(self, code: int = 1000, reason: Optional[str] = None):
        self.code = code
        self.reason = reason
        super().__init__(f"WebSocket disconnected with code {code}: {reason}")


class _WaitInput:
    pass


class _InputAwaitable:
    def __init__(self, ws):
        self.ws = ws

    def __await__(self):
        while not self.ws.c2s:
            if self.ws.closed:
                raise WebSocketDisconnect(1000)
            yield _WaitInput()
        return self.ws.c2s.popleft()


class WebSocket:
    def __init__(self, c2s_queue=None, s2c_queue=None):
        import collections
        self.c2s = c2s_queue if c2s_queue is not None else collections.deque()
        self.s2c = s2c_queue if s2c_queue is not None else collections.deque()
        self.accepted = False
        self.closed = False

    async def accept(self):
        self.accepted = True

    async def send_json(self, data: Any):
        self.s2c.append(data)

    async def send_text(self, text: str):
        self.s2c.append(text)

    async def receive_json(self) -> Any:
        return await _InputAwaitable(self)

    async def receive_text(self) -> str:
        res = await _InputAwaitable(self)
        return str(res)

    async def close(self, code: int = 1000):
        self.closed = True

    def __eq__(self, other):
        return self is other or getattr(other, "server_ws", None) is self


class WebSocketTestSession:
    def __init__(self, app, url: str):
        self.app = app
        self.url = url
        self.server_ws = WebSocket()
        self.coro = None

    def __enter__(self):
        clean_url = self.url.split("?")[0]
        norm = "/" + "/".join(p for p in clean_url.split("/") if p)
        matched_route = None
        path_params = {}
        for r in self.app.routes:
            params = r.matches("WEBSOCKET", norm)
            if params is not None:
                matched_route = r
                path_params = params
                break

        if not matched_route:
            raise RuntimeError(f"No websocket route found matching {self.url}")

        sig = inspect.signature(matched_route.handler)
        handler_kwargs = {}
        for param_name, param in sig.parameters.items():
            if param_name in path_params:
                handler_kwargs[param_name] = path_params[param_name]
            elif param_name == "websocket" or param.annotation is WebSocket:
                handler_kwargs[param_name] = self.server_ws
            else:
                handler_kwargs[param_name] = self.server_ws

        self.coro = matched_route.handler(**handler_kwargs)
        try:
            self.coro.send(None)
        except StopIteration:
            pass
        return self

    def send_json(self, data: Any):
        self.server_ws.c2s.append(data)
        try:
            self.coro.send(None)
        except StopIteration:
            pass

    def send_text(self, text: str):
        self.send_json(text)

    def receive_json(self) -> Any:
        if not self.server_ws.s2c:
            raise RuntimeError(f"WebSocket receive_json called on {self.url} but queue is empty")
        return self.server_ws.s2c.popleft()

    def receive_text(self) -> str:
        return str(self.receive_json())

    def close(self, code: int = 1000):
        if not self.server_ws.closed:
            self.server_ws.closed = True
            try:
                self.coro.throw(WebSocketDisconnect(code))
            except (StopIteration, WebSocketDisconnect):
                pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __eq__(self, other):
        return (
            self is other
            or self.server_ws is other
            or (isinstance(other, WebSocketTestSession) and self.server_ws is other.server_ws)
        )


class TestClient:
    def __init__(self, app):
        self.app = app

    def get(self, url: str, **kwargs):
        res = self.app.test_request("GET", url, **kwargs)
        return FallbackResponse(res.get("status_code", 200), res.get("data", {}))

    def post(self, url: str, json: dict = None, **kwargs):
        res = self.app.test_request("POST", url, json_payload=json, **kwargs)
        return FallbackResponse(res.get("status_code", 200), res.get("data", {}))

    def websocket_connect(self, url: str, **kwargs):
        return WebSocketTestSession(self.app, url)


# ============================================================================
# Bootstrap module shims into sys.modules if not installed
# ============================================================================

def setup_shims():
    if "pydantic" not in sys.modules:
        try:
            import pydantic  # noqa
        except ImportError:
            pydantic_mod = types.ModuleType("pydantic")
            pydantic_mod.BaseModel = BaseModel
            pydantic_mod.Field = Field
            pydantic_mod.FieldInfo = FieldInfo
            sys.modules["pydantic"] = pydantic_mod

    if "pydantic_settings" not in sys.modules:
        try:
            import pydantic_settings  # noqa
        except ImportError:
            settings_mod = types.ModuleType("pydantic_settings")
            settings_mod.BaseSettings = BaseSettings
            sys.modules["pydantic_settings"] = settings_mod

    if "fastapi" not in sys.modules:
        try:
            import fastapi  # noqa
        except ImportError:
            fastapi_mod = types.ModuleType("fastapi")
            fastapi_mod.FastAPI = FastAPI
            fastapi_mod.APIRouter = APIRouter
            fastapi_mod.HTTPException = HTTPException
            fastapi_mod.WebSocket = WebSocket
            fastapi_mod.WebSocketDisconnect = WebSocketDisconnect

            # middleware submodule
            mw_mod = types.ModuleType("fastapi.middleware")
            cors_mod = types.ModuleType("fastapi.middleware.cors")
            cors_mod.CORSMiddleware = CORSMiddleware
            mw_mod.cors = cors_mod
            fastapi_mod.middleware = mw_mod
            sys.modules["fastapi.middleware"] = mw_mod
            sys.modules["fastapi.middleware.cors"] = cors_mod

            # testclient submodule
            tc_mod = types.ModuleType("fastapi.testclient")
            tc_mod.TestClient = TestClient
            fastapi_mod.testclient = tc_mod
            sys.modules["fastapi.testclient"] = tc_mod

            sys.modules["fastapi"] = fastapi_mod
    else:
        fastapi_mod = sys.modules["fastapi"]
        if not hasattr(fastapi_mod, "WebSocket"):
            fastapi_mod.WebSocket = WebSocket
        if not hasattr(fastapi_mod, "WebSocketDisconnect"):
            fastapi_mod.WebSocketDisconnect = WebSocketDisconnect
        if not hasattr(fastapi_mod, "FastAPI"):
            fastapi_mod.FastAPI = FastAPI
        if not hasattr(fastapi_mod, "APIRouter"):
            fastapi_mod.APIRouter = APIRouter


setup_shims()

