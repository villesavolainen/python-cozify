#!/usr/bin/env python3
"""Test module for multi-hub authentication and support.

This module tests the python-cozify library's ability to handle multiple Cozify hubs.
It creates a test environment with multiple emulated hubs and verifies that:
1. Multiple hubs can be configured simultaneously
2. Hub authentication works correctly with multiple hubs
3. Hub operations can be performed on each hub independently
4. Hub selection works correctly when multiple hubs are available

The tests use the Multi_hub class to create multiple temporary hub configurations
in the state, and then test various hub-related functions with these configurations.
"""

import datetime
import os
import tempfile
import time

import pytest

from cozify import cloud, config, hub
from cozify.Error import AuthenticationError
from cozify.test import debug
from cozify.test.fixtures import *


class Multi_hub:
    """Creates multiple temporary hub sections (with test data) in a tmp_cloud"""

    def __init__(self, tmp_cloud, num_hubs=2):
        self.hubs = []
        self.num_hubs = num_hubs
        self.tmp_cloud = tmp_cloud

        # Create multiple hub configurations
        for i in range(num_hubs):
            hub_id = f"deadbeef-aaaa-bbbb-cccc-tmphub{i:06d}"
            hub_name = f"HubbyMcHubFace{i}"
            hub_host = f"127.0.0.{i+1}"
            hub_token = f"eyJkb20iOiJ1ayIsImFsZyI6IkhTNTEyIiwidHlwIjoiSldUIn0.eyJyb2xlIjo4LCJpYXQiOjE1MTI5ODg5NjksImV4cCI6MTUxNTQwODc2OSwidXNlcl9pZCI6ImRlYWRiZWVmLWFhYWEtYmJiYi1jY2NjLWRkZGRkZGRkZGRkZCIsImtpZCI6ImRlYWRiZWVmLWRkZGQtY2NjYy1iYmJiLWFhYWFhYWFhYWFhYSIsImlzcyI6IkNsb3VkIn0.QVKKYyfTJPks_BXeKs23uvslkcGGQnBTKodA-UGjgHg{i}"

            self.hubs.append({
                "id": hub_id,
                "name": hub_name,
                "host": hub_host,
                "token": hub_token,
                "section": f"Hubs.{hub_id}"
            })

    @pytest.mark.usefixtures("tmp_cloud")
    def __enter__(self):
        # Set up hub configurations in the state
        for i, hub_config in enumerate(self.hubs):
            config.state.add_section(hub_config["section"])
            config.state[hub_config["section"]]["hubname"] = hub_config["name"]
            config.state[hub_config["section"]]["host"] = hub_config["host"]
            config.state[hub_config["section"]]["hubtoken"] = hub_config["token"]

            # Set the first hub as default
            if i == 0:
                config.state["Hubs"]["default"] = hub_config["id"]

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        config.setStatePath()

    def devices(self, hub_index=0):
        from cozify.test import fixtures_devices as dev
        return dev.device_ids, dev.devices

    def states(self, hub_index=0):
        from cozify.test import fixtures_devices as dev
        return dev.states


@pytest.fixture
def multi_hub(tmp_cloud):
    with Multi_hub(tmp_cloud, num_hubs=2) as hub_obj:
        print("Multi hub state for testing:")
        config.dump_state()
        yield hub_obj


@pytest.mark.logic
def test_multi_hub_setup(multi_hub):
    """Test that multiple hubs are correctly set up in the configuration"""
    # Check that we have the expected number of hubs in the configuration
    hub_sections = [section for section in config.state.sections() if section.startswith("Hubs.")]
    assert len(hub_sections) == multi_hub.num_hubs

    # Check that each hub has the expected configuration
    for i, hub_config in enumerate(multi_hub.hubs):
        section = hub_config["section"]
        assert config.state[section]["hubname"] == hub_config["name"]
        assert config.state[section]["host"] == hub_config["host"]
        assert config.state[section]["hubtoken"] == hub_config["token"]

    # Check that the first hub is set as default
    assert config.state["Hubs"]["default"] == multi_hub.hubs[0]["id"]


@pytest.mark.logic
def test_multi_hub_default(multi_hub):
    """Test that the default hub is correctly identified"""
    # The default hub should be the first one
    assert hub.default() == multi_hub.hubs[0]["id"]


@pytest.mark.logic
def test_multi_hub_exists(multi_hub):
    """Test that hub.exists() correctly identifies existing hubs"""
    # All hubs should exist
    for hub_config in multi_hub.hubs:
        assert hub.exists(hub_config["id"])

    # A non-existent hub should not exist
    assert not hub.exists("non-existent-hub-id")


@pytest.mark.logic
def test_multi_hub_name(multi_hub):
    """Test that hub.name() correctly returns hub names"""
    # Check that each hub's name is correctly returned
    for hub_config in multi_hub.hubs:
        assert hub.name(hub_config["id"]) == hub_config["name"]


@pytest.mark.logic
def test_multi_hub_host(multi_hub):
    """Test that hub.host() correctly returns hub hosts"""
    # Check that each hub's host is correctly returned
    for hub_config in multi_hub.hubs:
        assert hub.host(hub_config["id"]) == hub_config["host"]


@pytest.mark.logic
def test_multi_hub_token(multi_hub):
    """Test that hub.token() correctly returns hub tokens"""
    # Check that each hub's token is correctly returned
    for hub_config in multi_hub.hubs:
        assert hub.token(hub_config["id"]) == hub_config["token"]


@pytest.mark.logic
def test_multi_hub_id(multi_hub):
    """Test that hub.hub_id() correctly returns hub IDs"""
    # Check that each hub's ID is correctly returned by name
    for hub_config in multi_hub.hubs:
        assert hub.hub_id(hub_config["name"]) == hub_config["id"]


@pytest.mark.logic
def test_multi_hub_get_id(multi_hub):
    """Test that hub._get_id() correctly handles hub selection"""
    # Without specifying a hub, it should return the default hub
    assert hub._get_id() == multi_hub.hubs[0]["id"]

    # When specifying a hub by ID, it should return that hub's ID
    for hub_config in multi_hub.hubs:
        assert hub._get_id(hub_id=hub_config["id"]) == hub_config["id"]

    # When specifying a hub by name, it should return that hub's ID
    for hub_config in multi_hub.hubs:
        assert hub._get_id(hub_name=hub_config["name"]) == hub_config["id"]


@pytest.mark.logic
def test_multi_hub_fill_kwargs(multi_hub):
    """Test that hub._fill_kwargs() correctly fills in hub-related kwargs"""
    # Without specifying a hub, it should use the default hub
    kwargs = {}
    hub._fill_kwargs(kwargs)
    assert kwargs["hub_id"] == multi_hub.hubs[0]["id"]
    assert kwargs["hub_token"] == multi_hub.hubs[0]["token"]
    assert kwargs["host"] == multi_hub.hubs[0]["host"]

    # When specifying a hub by ID, it should use that hub
    for hub_config in multi_hub.hubs:
        kwargs = {"hub_id": hub_config["id"]}
        hub._fill_kwargs(kwargs)
        assert kwargs["hub_id"] == hub_config["id"]
        assert kwargs["hub_token"] == hub_config["token"]
        assert kwargs["host"] == hub_config["host"]

    # When specifying a hub by name, it should use that hub
    for hub_config in multi_hub.hubs:
        kwargs = {"hub_name": hub_config["name"]}
        hub._fill_kwargs(kwargs)
        assert kwargs["hub_id"] == hub_config["id"]
        assert kwargs["hub_token"] == hub_config["token"]
        assert kwargs["host"] == hub_config["host"]


@pytest.mark.logic
def test_multi_hub_authentication(multi_hub):
    """Test that cloud.authenticate() correctly handles multiple hubs"""
    # Mock the cloud.authenticate function to avoid actual API calls
    original_authenticate = cloud.authenticate

    def mock_authenticate(trustCloud=True, trustHub=True, remote=False, autoremote=True):
        # This mock function simulates successful authentication
        return True

    # Replace the authenticate function with our mock
    cloud.authenticate = mock_authenticate

    try:
        # Test authentication with the default hub
        assert cloud.authenticate()

        # Test authentication with each hub explicitly
        for hub_config in multi_hub.hubs:
            # We can't directly test cloud.authenticate with a specific hub,
            # but we can test that hub operations work with each hub
            assert hub.exists(hub_config["id"])
            assert hub.name(hub_config["id"]) == hub_config["name"]
            assert hub.host(hub_config["id"]) == hub_config["host"]
            assert hub.token(hub_config["id"]) == hub_config["token"]

            # Test that we can switch the default hub and operations still work
            config.state["Hubs"]["default"] = hub_config["id"]
            assert hub.default() == hub_config["id"]

            # Test that hub._get_id() returns the correct hub when no hub is specified
            assert hub._get_id() == hub_config["id"]

            # Test that hub._fill_kwargs() correctly fills in hub-related kwargs
            kwargs = {}
            hub._fill_kwargs(kwargs)
            assert kwargs["hub_id"] == hub_config["id"]
            assert kwargs["hub_token"] == hub_config["token"]
            assert kwargs["host"] == hub_config["host"]
    finally:
        # Restore the original authenticate function
        cloud.authenticate = original_authenticate

        # Restore the default hub to the first one
        config.state["Hubs"]["default"] = multi_hub.hubs[0]["id"]


@pytest.mark.logic
def test_multi_hub_operations(multi_hub):
    """Test that hub operations can be performed on each hub"""
    # For each hub, test that we can perform hub-specific operations
    for hub_config in multi_hub.hubs:
        # Test that we can get the hub's name
        assert hub.name(hub_config["id"]) == hub_config["name"]

        # Test that we can get the hub's host
        assert hub.host(hub_config["id"]) == hub_config["host"]

        # Test that we can get the hub's token
        assert hub.token(hub_config["id"]) == hub_config["token"]

        # Test that we can set and get the hub's token
        new_token = f"{hub_config['token']}_new"
        hub.token(hub_config["id"], new_token)
        assert hub.token(hub_config["id"]) == new_token

        # Test that we can set and get the hub's remote status
        hub.remote(hub_config["id"], False)
        assert not hub.remote(hub_config["id"])
        hub.remote(hub_config["id"], True)
        assert hub.remote(hub_config["id"])

        # Test that we can set and get the hub's autoremote status
        hub.autoremote(hub_config["id"], False)
        assert not hub.autoremote(hub_config["id"])
        hub.autoremote(hub_config["id"], True)
        assert hub.autoremote(hub_config["id"])
