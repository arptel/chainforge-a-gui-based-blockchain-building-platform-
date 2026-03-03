// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract DataStore {
    mapping(string => string) private data;

    event Stored(string key, string value);

    function store(string memory key, string memory value) public {
        data[key] = value;
        emit Stored(key, value);
    }

    function retrieve(string memory key) public view returns (string memory) {
        return data[key];
    }
}