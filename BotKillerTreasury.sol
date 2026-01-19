// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract BotKillerTreasury {
    event Received(address indexed from, uint256 amount);

    receive() external payable {
        emit Received(msg.sender, msg.value);
    }
}
