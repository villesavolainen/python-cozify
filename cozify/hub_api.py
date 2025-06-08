"""Module for all Cozify Hub API 1:1 calls

Attributes:
    apiPath(str): Hub API endpoint path including version. Things may suddenly stop working if a software update increases the API version on the Hub. Incrementing this value until things work will get you by until a new version is published.
"""

import json

import requests
from absl import logging

from cozify import cloud_api

from cozify.Error import APIError, ConnectionError

apiPath = "/cc/1.14"


def _getBase(host, port=8893, **kwargs):
    return "http://{0}:{1}".format(host, port)


def get(call, hub_token_header=True, base=apiPath, params=None, **kwargs):
    """GET method for calling hub API.

    Args:
        call(str): API path to call after apiPath, needs to include leading /.
        hub_token_header(bool): Set to False to omit hub_token usage in call headers.
        base(str): Base path to call from API instead of global apiPath. Defaults to apiPath.
        params(dict): Query parameters to include in the request.
        **host(str): ip address or hostname of hub.
        **hub_token(str): Hub authentication token.
        **remote(bool): If call is to be local or remote (bounced via cloud).
        **cloud_token(str): Cloud authentication token. Only needed if remote = True.
    """
    return _call(
        method=requests.get,
        call="{0}{1}".format(base, call),
        hub_token_header=hub_token_header,
        params=params,
        **kwargs
    )


def put(call, data, hub_token_header=True, base=apiPath, params=None, **kwargs):
    """PUT method for calling hub API. For rest of kwargs parameters see get()

    Args:
        call(str): API path to call after apiPath, needs to include leading /.
        data(str): json string to push out as the payload.
        hub_token_header(bool): Set to False to omit hub_token usage in call headers.
        base(str): Base path to call from API instead of global apiPath. Defaults to apiPath.
        params(dict): Query parameters to include in the request.
    """
    return _call(
        method=requests.put,
        call="{0}{1}".format(base, call),
        hub_token_header=hub_token_header,
        data=data,
        params=params,
        **kwargs
    )


def _call(*, call, method, hub_token_header, data=None, params=None, **kwargs):
    """Backend for get & put

    Args:
        call(str): Full API path to call.
        method(function): requests.get|put function to use for call.
        params(dict): Query parameters to include in the request.
    """
    response = None
    headers = {}
    if "headers" in kwargs:  # pragma: no cover
        raise ValueError("Headers already defined: {}".format(kwargs["headers"]))
    if hub_token_header:
        if "hub_token" not in kwargs:
            raise AttributeError(
                "Asked to do a call to the hub but no hub_token provided."
            )
        headers["Authorization"] = kwargs["hub_token"]
    if data is not None:
        data = json.dumps(data)
        headers["content-type"] = "application/json"

    if "remote" in kwargs and kwargs["remote"]:  # remote call
        if "cloud_token" not in kwargs:
            raise AttributeError("Asked to do remote call but no cloud_token provided.")
        headers["Authorization"] = kwargs["cloud_token"]
        headers["X-Hub-Key"] = kwargs["hub_token"]
        response = cloud_api.remote(apicall=call, data=data, headers=headers, params=params)
    else:  # local call
        if "host" not in kwargs or not kwargs["host"]:
            raise AttributeError(
                "Local call but no hostname was provided. Either set keyword remote or host."
            )
        try:
            response = method(
                _getBase(**kwargs) + call, headers=headers, data=data, params=params, timeout=5
            )
        except requests.exceptions.RequestException as e:  # pragma: no cover
            raise ConnectionError(str(e)) from None

    # evaluate response, wether it was remote or local
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 410:  # pragma: no cover
        raise APIError(
            response.status_code,
            "API version outdated. Update python-cozify. %s - %s - %s"
            % (response.reason, response.url, response.text),
        )
    else:  # pragma: no cover
        raise APIError(
            response.status_code,
            "%s - %s - %s" % (response.reason, response.url, response.text),
        )


def hub(**kwargs):
    """1:1 implementation of /hub API call. For kwargs see cozify.hub_api.get()

    Returns:
        dict: Hub state dict.
    """
    return get("hub", base="/", hub_token_header=False, **kwargs)


def tz(**kwargs):
    """1:1 implementation of /hub/tz API call. For kwargs see cozify.hub_api.get()

    Returns:
        str: Timezone of the hub, for example: 'Europe/Helsinki'
    """
    return get("/hub/tz", **kwargs)


def devices(**kwargs):
    """1:1 implementation of /devices API call. For remaining kwargs see cozify.hub_api.get()

    Args:
        **mock_devices(dict): If defined, returned as-is as if that were the result we received.

    Returns:
        dict: Full live device state as returned by the API
    """
    if "mock_devices" in kwargs:
        return kwargs["mock_devices"]

    return get("/devices", **kwargs)


def devices_command(command, **kwargs):
    """1:1 implementation of /devices/command. For kwargs see cozify.hub_api.put()

    Args:
        command(dict): dictionary of type DeviceData containing the changes wanted. Will be converted to json.

    Returns:
        str: What ever the API replied or raises an APIEerror on failure.
    """
    logging.debug("command json to send: {0}".format(command))
    return put("/devices/command", command, **kwargs)


def devices_command_generic(*, device_id, command=None, request_type, **kwargs):
    """Command helper for CMD type of actions.
    No checks are made wether the device supports the command or not. For kwargs see cozify.hub_api.put()

    Args:
        device_id(str): ID of the device to operate on.
        request_type(str): Type of CMD to run, e.g. CMD_DEVICE_OFF
        command(dict): Optional dictionary to override command sent. Defaults to None which is interpreted as { device_id, type }
    Returns:
        str: What ever the API replied or raises an APIError on failure.
    """
    if command is None:
        command = [{"id": device_id, "type": request_type}]
    return devices_command(command, **kwargs)


def devices_command_state(*, device_id, state, **kwargs):
    """Command helper for CMD type of actions.
    No checks are made wether the device supports the command or not. For kwargs see cozify.hub_api.put()

    Args:
        device_id(str): ID of the device to operate on.
        state(dict): New state dictionary containing changes.
    Returns:
        str: What ever the API replied or raises an APIError on failure.
    """
    command = [{"id": device_id, "type": "CMD_DEVICE", "state": state}]
    return devices_command(command, **kwargs)


def devices_command_on(device_id, **kwargs):
    """Command helper for CMD_DEVICE_ON.

    Args:
        device_id(str): ID of the device to operate on.
    Returns:
        str: What ever the API replied or raises an APIError on failure.
    """
    return devices_command_generic(
        device_id=device_id, request_type="CMD_DEVICE_ON", **kwargs
    )


def devices_command_off(device_id, **kwargs):
    """Command helper for CMD_DEVICE_OFF.

    Args:
        device_id(str): ID of the device to operate on.
    Returns:
        str: What ever the API replied or raises an APIException on failure.
    """
    return devices_command_generic(
        device_id=device_id, request_type="CMD_DEVICE_OFF", **kwargs
    )


def scenes(**kwargs):
    """Implementation of /scenes API call. For kwargs see cozify.hub_api.get()

    Returns:
        dict: Full scene state as returned by the API
    """
    return get("/scenes", **kwargs)


def scenes_command_state(*, scene_id, request_type, **kwargs):
    """Commands changing a scene's state. For kwargs see cozify.hub_api.put()

    Args:
        scene_id(str): ID of the scene to operate on.
        request_type(str): the request type, i.e. CMD_SCENE_ON or CMD_SCENE_OFF.
    Returns:
        str: Whatever the API replied or raises an APIError on failure.
    """
    command = [{"id": scene_id, "type": request_type}]
    logging.debug("command json to send: {0}".format(command))
    return put("/scenes/command", command, **kwargs)


def scenes_command_off(scene_id, **kwargs):
    """Command helper for CMD_SCENE_OFF.

    Args:
        scene_id(str): ID of the scene to operate on.
    Returns:
        str: What ever the API replied or raises an APIException on failure.
    """
    return scenes_command_state(
        scene_id=scene_id, request_type="CMD_SCENE_OFF", **kwargs
    )


def scenes_command_on(scene_id, **kwargs):
    """Command helper for CMD_SCENE_ON.

    Args:
        scene_id(str): ID of the scene to operate on.
    Returns:
        str: What ever the API replied or raises an APIException on failure.
    """
    return scenes_command_state(
        scene_id=scene_id, request_type="CMD_SCENE_ON", **kwargs
    )


def groups(**kwargs):
    """Implementation of /groups API call. For kwargs see cozify.hub_api.get()

    Returns:
        dict: Full groups state as returned by the API
    """
    return get("/groups", **kwargs)


def groups_command(command, **kwargs):
    """1:1 implementation of /groups/command. For kwargs see cozify.hub_api.put()

    Args:
        command(dict): dictionary containing the changes wanted. Will be converted to json.

    Returns:
        str: What ever the API replied or raises an APIError on failure.
    """
    logging.debug("command json to send: {0}".format(command))
    return put("/groups/command", command, **kwargs)


def groups_command_state(*, group_id, request_type, **kwargs):
    """Commands changing a group's state. For kwargs see cozify.hub_api.put()

    Args:
        group_id(str): ID of the group to operate on.
        request_type(str): the request type, i.e. CMD_GROUP_ON or CMD_GROUP_OFF.
    Returns:
        str: Whatever the API replied or raises an APIError on failure.
    """
    command = [{"id": group_id, "type": request_type}]
    logging.debug("command json to send: {0}".format(command))
    return put("/groups/command", command, **kwargs)


def groups_command_off(group_id, **kwargs):
    """Command helper for CMD_GROUP_OFF.

    Args:
        group_id(str): ID of the group to operate on.
    Returns:
        str: What ever the API replied or raises an APIException on failure.
    """
    return groups_command_state(
        group_id=group_id, request_type="CMD_GROUP_OFF", **kwargs
    )


def groups_command_on(group_id, **kwargs):
    """Command helper for CMD_GROUP_ON.

    Args:
        group_id(str): ID of the group to operate on.
    Returns:
        str: What ever the API replied or raises an APIException on failure.
    """
    return groups_command_state(
        group_id=group_id, request_type="CMD_GROUP_ON", **kwargs
    )


def rules(**kwargs):
    """Implementation of /rules API call. For kwargs see cozify.hub_api.get()

    Returns:
        dict: Full rules state as returned by the API
    """
    return get("/rules", **kwargs)


def rules_command(command, **kwargs):
    """1:1 implementation of /rules/command. For kwargs see cozify.hub_api.put()

    Args:
        command(dict): dictionary containing the changes wanted. Will be converted to json.

    Returns:
        str: What ever the API replied or raises an APIError on failure.
    """
    logging.debug("command json to send: {0}".format(command))
    return put("/rules/command", command, **kwargs)


def rules_command_state(*, rule_id, request_type, **kwargs):
    """Commands changing a rule's state. For kwargs see cozify.hub_api.put()

    Args:
        rule_id(str): ID of the rule to operate on.
        request_type(str): the request type, i.e. CMD_RULE_ON or CMD_RULE_OFF.
    Returns:
        str: Whatever the API replied or raises an APIError on failure.
    """
    command = [{"id": rule_id, "type": request_type}]
    logging.debug("command json to send: {0}".format(command))
    return put("/rules/command", command, **kwargs)


def rules_command_off(rule_id, **kwargs):
    """Command helper for CMD_RULE_OFF.

    Args:
        rule_id(str): ID of the rule to operate on.
    Returns:
        str: What ever the API replied or raises an APIException on failure.
    """
    return rules_command_state(
        rule_id=rule_id, request_type="CMD_RULE_OFF", **kwargs
    )


def rules_command_on(rule_id, **kwargs):
    """Command helper for CMD_RULE_ON.

    Args:
        rule_id(str): ID of the rule to operate on.
    Returns:
        str: What ever the API replied or raises an APIException on failure.
    """
    return rules_command_state(
        rule_id=rule_id, request_type="CMD_RULE_ON", **kwargs
    )


def devices_configuration(device_id=None, **kwargs):
    """Implementation of /devices/configuration API call. For kwargs see cozify.hub_api.get()

    Args:
        device_id(str): Optional ID of the device to get configuration for.
    Returns:
        dict: Device configuration as returned by the API
    """
    params = {}
    if device_id:
        params = {"deviceId": device_id}
    return get("/devices/configuration", params=params, **kwargs)


def devices_configuration_save(configuration, **kwargs):
    """Implementation of /devices/configuration API call. For kwargs see cozify.hub_api.put()

    Args:
        configuration(dict): Device configuration to save.
    Returns:
        str: What ever the API replied or raises an APIError on failure.
    """
    return put("/devices/configuration", configuration, **kwargs)


def hub_autoconfig(configuration, **kwargs):
    """Implementation of /hub/autoconfig API call. For kwargs see cozify.hub_api.put()

    Args:
        configuration(dict): Configuration data to apply.
    Returns:
        bool: True on success, otherwise error
    """
    return put("/hub/autoconfig", configuration, **kwargs)


def users(**kwargs):
    """1:1 implementation of /users API call.
    Returns:
        dict:
    """
    return get("/hub/users", **kwargs)


def hub_poll(ts=None, device_ts=None, group_ts=None, scene_ts=None, rule_ts=None, activator_ts=None, cozify_uuid=None, **kwargs):
    """Implementation of /hub/poll API call. For kwargs see cozify.hub_api.get()

    Args:
        ts(int): Timestamp for all data. If specified result contains all hub data that has changed after the timestamp.
        device_ts(int): Timestamp for device data. If specified result contains device data that has changed after this timestamp.
        group_ts(int): Timestamp for group data. If specified result contains group data that has changed after this timestamp.
        scene_ts(int): Timestamp for scene data. If specified result contains scene data that has changed after this timestamp.
        rule_ts(int): Timestamp for rule data. If specified result contains rule data that has changed after this timestamp.
        activator_ts(int): Timestamp for activator data.
        cozify_uuid(str): Client application identifier.
    Returns:
        list: List of Delta objects indicating changes since the specified timestamps.
    """
    params = {}
    if ts is not None:
        params["ts"] = ts
    if device_ts is not None:
        params["deviceTs"] = device_ts
    if group_ts is not None:
        params["groupTs"] = group_ts
    if scene_ts is not None:
        params["sceneTs"] = scene_ts
    if rule_ts is not None:
        params["ruleTs"] = rule_ts
    if activator_ts is not None:
        params["activatorTs"] = activator_ts
    if cozify_uuid is not None:
        params["cozify_uuid"] = cozify_uuid

    return get("/hub/poll", params=params, **kwargs)
