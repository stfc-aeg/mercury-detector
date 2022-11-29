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
        logging.warning("target_path: {}".format(target_path))

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


class GPIBProxyContext(ProxyContext):
    def __init__(self, proxy):
        super().__init__(proxy, 'gpib')

        # Force-create some non-wrapped attributes
        self.setattr("_psu_path", None, wrap=False)
        self.setattr("_peltier_path", None, wrap=False)

    def _list_devices(self):
        return self.get('device_ids')

    def identify_devices(self):
        devices = self._list_devices()

        psu_info = None
        peltier_info = None

        for i in range(0, len(devices)):    # Looping by device directly doesn't work...
            device = devices[i]
            if 'K2410' in device:
                self.setattr("_psu_path", 'devices/{}'.format(device), wrap=False)
                psu_info = {
                        'path' : self._psu_path,
                        'ident' : self.get('{}/ident'.format(self._psu_path))
                        }
            elif 'K2510' in device:
                self.setattr("_peltier_path", 'devices/{}'.format(device), wrap=False)
                peltier_info = {
                        'path' : self._peltier_path,
                        'ident' : self.get('{}/ident'.format(self._peltier_path))
                        }

        devices = {
            'psu': psu_info,
            'peltier' : peltier_info
        }
        logging.debug('GPIB Proxy detected devices: {}'.format(devices))

        return devices

    def psu_status(self):
        return self.get(self._psu_path)

    def peltier_status(self):
        return self.get(self._peltier__path)

    def get_psu_controlled(self):
        return self.get('{}/device_control_state'.format(self._psu_path))

    def get_peltier_controlled(self):
        return self.get('{}/device_control_state'.format(self._peltier_path))

    def set_psu_output_state(self, enabled=True):
        if self._psu_path is None:
            self.identify_devices()
        if not self.get_psu_controlled():
            raise Exception("PSU not under control")

        response = self.set('{}'.format(self._psu_path), {
            'output_state': enabled
        })

        return response

    def get_psu_voltage_measurement(self):
        if self._psu_path is None:
            self.identify_devices()
        return self.get('{}/voltage/voltage_measurement'.format(self._psu_path))

    def get_psu_current_measurement(self):
        if self._psu_path is None:
            self.identify_devices()
        return self.get('{}/current/current_measurement'.format(self._psu_path))
