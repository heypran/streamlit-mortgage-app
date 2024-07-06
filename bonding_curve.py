import json
import streamlit as st
import matplotlib.pyplot as plt
from web3 import Web3

# Streamlit app
st.title('Bonding Curve Plot')

# Select RPC URL
rpc_url_options = ['https://rpc-amoy.polygon.technology','http://127.0.0.1:8545']
rpc_url = st.selectbox('Select RPC URL:', rpc_url_options)

# Connect to Ethereum node
w3 = Web3(Web3.HTTPProvider(rpc_url))

# Contract ABI
contract_abi = json.loads('''[
  {
    "inputs": [
      { "internalType": "string", "name": "name", "type": "string" },
      { "internalType": "string", "name": "symbol", "type": "string" },
      { "internalType": "uint256", "name": "_initialSupply", "type": "uint256" },
      { "internalType": "uint256", "name": "_initialPricePerToken", "type": "uint256" }
    ],
    "stateMutability": "nonpayable",
    "type": "constructor"
  },
  {
    "inputs": [
      { "internalType": "uint256", "name": "_ethAmount", "type": "uint256" }
    ],
    "name": "calculatePurchaseReturn",
    "outputs": [
      { "internalType": "uint256", "name": "", "type": "uint256" }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [
      { "internalType": "uint256", "name": "_tokenAmount", "type": "uint256" }
    ],
    "name": "calculateSaleReturn",
    "outputs": [
      { "internalType": "uint256", "name": "", "type": "uint256" }
    ],
    "stateMutability": "view",
    "type": "function"
  }
]''')

# Input for contract address
contract_address = st.text_input('Enter Contract Address:', '0x43B8DBeDD4138A0a9a0a6F6b5A4cAba8ae74FB0D')

# Connect to the contract
if Web3.is_address(contract_address):
    contract_address = Web3.to_checksum_address(contract_address)
    contract = w3.eth.contract(address=contract_address, abi=contract_abi)

    # Input fields for ETH amount
    eth_amount = st.number_input('Enter ETH amount for Purchase:', min_value=0.0, step=0.01)

    # Button to calculate token amount
    if st.button('Calculate Token Amount for Purchase'):
        try:
            eth_amount_wei = Web3.to_wei(eth_amount, 'ether')
            token_amount = contract.functions.calculatePurchaseReturn(eth_amount_wei).call()
            st.write(f'Token Amount: {Web3.from_wei(token_amount, "ether")}')
        except Exception as e:
            st.error(f"Error: {str(e)}")

    # Generate bonding curve for purchase
    try:
        eth_values = [i for i in range(1, 101)]  # ETH amounts from 1 to 100
        token_values = []

        for eth in eth_values:
            eth_wei = Web3.to_wei(eth, 'ether')
            token_amount = contract.functions.calculatePurchaseReturn(eth_wei).call()
            token_values.append(Web3.from_wei(token_amount, 'ether'))

        # Plot bonding curve for purchase
        plt.figure(figsize=(10, 5))
        plt.plot(token_values, eth_values, label='Purchase Bonding Curve')
        plt.xlabel('Token Amount')
        plt.ylabel('ETH Amount')
        plt.title('Purchase Bonding Curve')
        plt.legend()
        st.pyplot(plt)
    except Exception as e:
        st.error(f"Error generating purchase bonding curve: {str(e)}")

    # Input fields for Token amount
    token_amount_sale = st.number_input('Enter Token amount for Sale:', min_value=0.0, step=0.01)

    # Button to calculate ETH amount for sale
    if st.button('Calculate ETH Amount for Sale'):
        try:
            token_amount_wei = Web3.to_wei(token_amount_sale, 'ether')
            eth_amount_sale = contract.functions.calculateSaleReturn(token_amount_wei).call()
            st.write(f'ETH Amount: {Web3.from_wei(eth_amount_sale, "ether")}')
        except Exception as e:
            st.error(f"Error: {str(e)}")

    # Generate bonding curve for sale
    try:
        token_values_sale = [i for i in range(1, 101)]  # Token amounts from 1 to 100
        eth_values_sale = []

        for token in token_values_sale:
            token_wei = Web3.to_wei(token, 'ether')
            eth_amount_sale = contract.functions.calculateSaleReturn(token_wei).call()
            eth_values_sale.append(Web3.from_wei(eth_amount_sale, 'ether'))

        # Plot bonding curve for sale
        plt.figure(figsize=(10, 5))
        plt.plot(token_values_sale, eth_values_sale, label='Sale Bonding Curve', color='orange')
        plt.xlabel('Token Amount')
        plt.ylabel('ETH Amount')
        plt.title('Sale Bonding Curve')
        plt.legend()
        st.pyplot(plt)
    except Exception as e:
        st.error(f"Error generating sale bonding curve: {str(e)}")
else:
    st.write("Please enter a valid contract address.")
