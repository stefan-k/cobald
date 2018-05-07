import time
import logging
import subprocess


def query_limits(query_command, key_transform):
    resource_limits = {}
    for item in subprocess.check_output(query_command, universal_newlines=True):
        key, _, value = (value.strip() for value in item.partition('='))
        try:
            resource = key_transform(key)
        except ValueError:
            continue
        else:
            resource_limits[resource] = float(value)
    return resource_limits


class ConcurrencyConstraintView(object):
    def __init__(self, pool: str = None, max_age: float = 30.):
        self._logger = logging.getLogger('condor_limits.constraints')
        self.pool = pool
        self.max_age = max_age
        self._valid_date = 0
        self._constraints = {}

    def __getitem__(self, resource: str) -> float:
        if self._valid_date < time.time():
            self._query_constraints()
        try:
            return self._constraints[resource]
        except KeyError:
            if '.' in resource:
                return self._constraints[resource.split('.')[0]]  # check parent group of resource
            raise

    def __setitem__(self, key: str, value: float):
        self._set_constraint(key, value)

    @staticmethod
    def _key_to_resource(key: str) -> str:
        if key.lower[-6:] == '_limit':
            return key[:-6]
        raise ValueError

    def _query_constraints(self):
        query_command = ['condor_config_val', '-negotiator', '-dump', 'LIMIT']
        if self.pool:
            query_command.extend(('-pool', str(self.pool)))
        resource_limits = query_limits(query_command, key_transform=self._key_to_resource)
        self._valid_date = self.max_age + time.time()
        self._constraints = resource_limits

    def _set_constraint(self, resource: str, constraint: float):
        reconfig_command = ['condor_config_val', '-negotiator']
        if self.pool:
            reconfig_command.extend(('-pool', str(self.pool)))
        reconfig_command.extend(('-rset', '%s_LIMIT = %s' % (resource, int(constraint))))
        try:
            subprocess.check_call(reconfig_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as err:
            self._logger.error('failed to constraint %r to %r', resource, constraint, exc_info=err)
        else:
            self._constraints[resource] = constraint


class ConcurrencyUsageView(object):
    def __init__(self, pool: str = None, max_age: float = 30.):
        self.pool = pool
        self.max_age = max_age
        self._valid_date = 0
        self._usage = {}

    def __getitem__(self, resource: str) -> float:
        if self._valid_date < time.time():
            self._query_usage()
        try:
            return self._usage[resource.replace('.', '_')]
        except KeyError:
            if '.' in resource:
                return self._usage[resource.split('.')[0]]  # check parent group of resource
            raise

    @staticmethod
    def _key_to_resource(key: str) -> str:
        if key.startswith('ConcurrencyLimit'):
            return key[16:]
        raise ValueError

    def _query_usage(self):
        query_command = ['condor_userprio', '-negotiator', '-long']
        if self.pool:
            query_command.extend(('-pool', str(self.pool)))
        resource_usage = query_limits(query_command, key_transform=self._key_to_resource)
        self._valid_date = self.max_age + time.time()
        self._usage = resource_usage

    def __str__(self):
        if self._valid_date < time.time():
            self._query_usage()
        return str(self._usage)

    def __repr__(self):
        return '%s(pool=%s, max_age=%s)' % (self.__class__.__name__, self.pool, self.max_age)


__all__ = [ConcurrencyConstraintView.__name__, ConcurrencyUsageView.__name__]
