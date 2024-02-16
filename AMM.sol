// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.17;

import "@openzeppelin/contracts/access/AccessControl.sol"; //This allows role-based access control through _grantRole() and the modifier onlyRole
import "@openzeppelin/contracts/token/ERC20/ERC20.sol"; //This contract needs to interact with ERC20 tokens

contract AMM is AccessControl{
    bytes32 public constant LP_ROLE = keccak256("LP_ROLE");
	uint256 public invariant;
	address public tokenA;
	address public tokenB;
	uint256 feebps = 3; //The fee in basis points (i.e., the fee should be feebps/10000)

	event Swap( address indexed _inToken, address indexed _outToken, uint256 inAmt, uint256 outAmt );
	event LiquidityProvision( address indexed _from, uint256 AQty, uint256 BQty );
	event Withdrawal( address indexed _from, address indexed recipient, uint256 AQty, uint256 BQty );

	/*
		Constructor sets the addresses of the two tokens
	*/
    constructor( address _tokenA, address _tokenB ) {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender );
        _grantRole(LP_ROLE, msg.sender);

		require( _tokenA != address(0), 'Token address cannot be 0' );
		require( _tokenB != address(0), 'Token address cannot be 0' );
		require( _tokenA != _tokenB, 'Tokens cannot be the same' );
		tokenA = _tokenA;
		tokenB = _tokenB;

    }


	function getTokenAddress( uint256 index ) public view returns(address) {
		require( index < 2, 'Only two tokens' );
		if( index == 0 ) {
			return tokenA;
		} else {
			return tokenB;
		}
	}

	/*
		The main trading functions
		
		User provides sellToken and sellAmount

		The contract must calculate buyAmount using the formula:
	*/
	function tradeTokens( address sellToken, uint256 sellAmount ) public {
		require(invariant > 0, 'Invariant must be nonzero');
		require(sellToken == tokenA || sellToken == tokenB, 'Invalid token');
		require(sellAmount > 0, 'Cannot trade 0');

		ERC20 sellTokenInstance = ERC20(sellToken);
		ERC20 buyTokenInstance = ERC20(sellToken == tokenA ? tokenB : tokenA);

		// Directly use balances in the calculations to reduce local variables
		uint256 sellTokenReserve = sellTokenInstance.balanceOf(address(this));
		uint256 buyTokenReserve = buyTokenInstance.balanceOf(address(this));
		uint256 feeAmount = (sellAmount * feebps) / 10000;

		// Inline calculation for sellAmountAfterFee to reduce variables
		uint256 buyAmount = buyTokenReserve - (invariant / (sellTokenReserve + (sellAmount - feeAmount)));

		require(buyAmount > 0, "Insufficient output amount");
		require(sellTokenInstance.transferFrom(msg.sender, address(this), sellAmount), "Failed to transfer sell tokens");
		require(buyTokenInstance.transfer(msg.sender, buyAmount), "Failed to transfer buy tokens");

//		// Update invariant directly to minimize variable usage
//		invariant = (sellTokenReserve + (sellAmount - feeAmount)) * (buyTokenReserve - buyAmount);
//		require(invariant >= sellTokenReserve * buyTokenReserve, 'Bad trade');
//

		uint256 new_invariant = ERC20(tokenA).balanceOf(address(this))*ERC20(tokenB).balanceOf(address(this));
		require( new_invariant >= invariant, 'Bad trade' );
		invariant = new_invariant;

		emit Swap(sellToken, address(buyTokenInstance), sellAmount, buyAmount);
	}

	/*
		Use the ERC20 transferFrom to "pull" amtA of tokenA and amtB of tokenB from the sender
	*/
	function provideLiquidity( uint256 amtA, uint256 amtB ) public {
		require( amtA > 0 || amtB > 0, 'Cannot provide 0 liquidity' );

		ERC20(tokenA).transferFrom(msg.sender, address(this), amtA);
		ERC20(tokenB).transferFrom(msg.sender, address(this), amtB);

		if (invariant == 0) {
			invariant = amtA * amtB;
		} else {
			invariant = ERC20(tokenA).balanceOf(address(this)) * ERC20(tokenB).balanceOf(address(this));
		}

		emit LiquidityProvision( msg.sender, amtA, amtB );
	}

	/*
		Use the ERC20 transfer function to send amtA of tokenA and amtB of tokenB to the target recipient
		The modifier onlyRole(LP_ROLE) 
	*/
	function withdrawLiquidity( address recipient, uint256 amtA, uint256 amtB ) public onlyRole(LP_ROLE) {
		require( amtA > 0 || amtB > 0, 'Cannot withdraw 0' );
		require( recipient != address(0), 'Cannot withdraw to 0 address' );
		if( amtA > 0 ) {
			ERC20(tokenA).transfer(recipient,amtA);
		}
		if( amtB > 0 ) {
			ERC20(tokenB).transfer(recipient,amtB);
		}
		invariant = ERC20(tokenA).balanceOf(address(this))*ERC20(tokenB).balanceOf(address(this));
		emit Withdrawal( msg.sender, recipient, amtA, amtB );
	}

	function ownerWithdraw() public onlyRole(LP_ROLE) {
		uint256 balanceA = ERC20(tokenA).balanceOf(address(this));
		uint256 balanceB = ERC20(tokenB).balanceOf(address(this));

		require(balanceA > 0 || balanceB > 0, 'No liquidity to withdraw');

		ERC20(tokenA).transfer(msg.sender, balanceA);
		ERC20(tokenB).transfer(msg.sender, balanceB);

		invariant = 0; // Reset invariant as liquidity is removed

		emit Withdrawal(msg.sender, msg.sender, balanceA, balanceB);
}


}
