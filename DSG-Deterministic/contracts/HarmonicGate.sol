// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract HarmonicGate {

    enum Grade { HG0, HG1, HG2, HG3, HG4 }

    function validate(Grade grade, uint256 stake) public pure returns (bool) {
        if (grade == Grade.HG0) return true;
        if (grade == Grade.HG1 && stake > 0) return true;
        if (grade == Grade.HG2 && stake >= 1 ether) return true;
        if (grade == Grade.HG3 && stake >= 5 ether) return true;
        if (grade == Grade.HG4 && stake >= 10 ether) return true;
        return false;
    }
}
