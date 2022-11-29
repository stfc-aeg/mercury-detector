import asyncio
import logging

from odin.adapters.parameter_tree import ParameterTreeError

from .context import SyncContext


class ProxyContext(SyncContext):

    def __init__(self, proxy, target):

        super().__init__()

        self.__dict__["proxy"] = proxy
        self.__dict__["target"] = target

        self.get = self._proxy_get
        self.set = self._proxy_set

    def _target_path(self, path):

        return f"{self.target}/{path}" if path else self.target

    async def _proxy_get(self, path=None):
        
        target_path = self._target_path(path)

        await asyncio.gather(*self.proxy.proxy_get(target_path, False))
        response = self._resolve_response(target_path)

        return response

    async def _proxy_set(self, path, data):

        target_path = self._target_path(path)

        await asyncio.gather(*self.proxy.proxy_set(target_path, data))
        response = self._resolve_response(target_path)

        return response

    def _resolve_response(self, path):

        try:
            elem = path.split('/')[-1]
            response = self.proxy.param_tree.get(path)[elem]
        except ParameterTreeError as e:
            logging.error("Proxy get failed with error: %s", str(e))
            response = None

        return response

        
class MunirProxyContext(ProxyContext):

    def __init__(self, proxy):
        super().__init__(proxy, 'munir')

    def execute_capture(self, file_path, file_name):

        response = self.set('', {
            'args': {'file_path': file_path, 'file_name': file_name},
            'execute': True
        })

        return response

    def get_status(self):

        return self.get('status')

    def is_executing(self):

        status = self.get_status()
        return status['executing']