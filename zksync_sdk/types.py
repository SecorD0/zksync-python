import abc
from dataclasses import dataclass
from decimal import Decimal
from enum import IntEnum
from typing import List, Optional, Union

from zksync_sdk.serialize_utils import (int_to_bytes, packed_amount_checked, packed_fee_checked,
                                        serialize_account_id,
                                        serialize_address, serialize_nonce, serialize_timestamp,
                                        serialize_token_id, )

TokenLike = Union[str, int]


@dataclass
class TxEthSignature:
    # type: 'EthereumSignature' | 'EIP1271Signature'
    type: str
    signature: str

    def __init__(self, type: str, signature: bytes):
        self.signature = signature.hex()
        self.type = type

    def dict(self):
        return {
            "type":      self.type,
            "signature": self.signature
        }


@dataclass
class Token:
    address: str
    id: int
    symbol: str
    decimals: int
    DefaultAddress = "0x0000000000000000000000000000000000000000"

    @classmethod
    def eth(cls):
        return cls(id=0,
                   address=Token.DefaultAddress,
                   symbol="ETH",
                   decimals=18)

    def decimal_amount(self, amount: int) -> Decimal:
        return Decimal(amount).scaleb(-self.decimals)

    def from_decimal(self, amount: Decimal) -> int:
        return int(amount.scaleb(self.decimals))

    def decimal_str_amount(self, amount: int) -> str:
        d = self.decimal_amount(amount)
        if d != Decimal(0):
            return str(d).rstrip("0")
        else:
            return str(d)


@dataclass
class TxSignature:
    public_key: str
    signature: str

    def __init__(self, public_key: bytes, signature: bytes):
        self.public_key = public_key.hex()
        self.signature = signature.hex()

    def dict(self):
        return {
            "pubKey":    self.public_key,
            "signature": self.signature
        }


class EncodedTx(abc.ABC):
    @abc.abstractmethod
    def encoded_message(self) -> bytes:
        pass

    @abc.abstractmethod
    def human_readable_message(self) -> str:
        pass

    @abc.abstractmethod
    def tx_type(self) -> int:
        pass

    @abc.abstractmethod
    def dict(self):
        pass


class ChainId(IntEnum):
    MAINNET = 1
    RINKEBY = 4
    ROPSTEN = 3
    LOCALHOST = 9


class ECDSAEthAuthData:
    pass


@dataclass
class ChangePubKey(EncodedTx):
    account_id: int
    account: str
    new_pk_hash: str
    token: Token
    fee: int
    nonce: int
    valid_from: int
    valid_until: int
    eth_auth_data: str
    eth_signature: TxEthSignature = None
    zk_sync_signature: TxSignature = None

    def human_readable_message(self) -> str:
        message = f"Set signing key: {self.new_pk_hash.replace('sync:', '').lower()}"
        if self.fee:
            message += f"\nFee: {self.fee} {self.token.symbol}"
        return message

    def encoded_message(self) -> bytes:
        return b"".join([
            int_to_bytes(self.tx_type(), 1),
            serialize_account_id(self.account_id),
            serialize_address(self.account),
            serialize_address(self.new_pk_hash),
            serialize_token_id(self.token.id),
            packed_fee_checked(self.fee),
            serialize_nonce(self.nonce),
            serialize_timestamp(self.valid_from),
            serialize_timestamp(self.valid_until)
        ])

    def dict(self):
        return {
            "type":       "ChangePubKey",
            "accountId":  self.account_id,
            "account":    self.account,
            "newPkHash":  self.new_pk_hash,
            "fee_token":  self.token.id,
            "fee":        self.fee,
            "nonce":      self.nonce,
            "signature":  self.signature.dict(),
            "amount":     self.amount,
            "validFrom":  self.valid_from,
            "validUntil": self.valid_until,
        }

    @classmethod
    def tx_type(cls):
        return 7


@dataclass
class Transfer(EncodedTx):
    account_id: int
    from_address: str
    to_address: str
    token: Token
    amount: int
    fee: int
    nonce: int
    valid_from: int
    valid_until: int
    signature: TxSignature = None

    def tx_type(self) -> int:
        return 5

    def human_readable_message(self) -> str:
        message = f"Transfer {self.token.decimal_str_amount(self.amount)} {self.token.symbol} to: {self.to_address.lower()}\nFee: {self.token.decimal_str_amount(self.fee)} {self.token.symbol}\nNonce: {self.nonce}"
        return message

    def encoded_message(self) -> bytes:
        return b"".join([
            int_to_bytes(self.tx_type(), 1),
            serialize_account_id(self.account_id),
            serialize_address(self.from_address),
            serialize_address(self.to_address),
            serialize_token_id(self.token.id),
            packed_amount_checked(self.amount),
            packed_fee_checked(self.fee),
            serialize_nonce(self.nonce),
            serialize_timestamp(self.valid_from),
            serialize_timestamp(self.valid_until)
        ])

    def dict(self):
        return {
            "type":       "Transfer",
            "accountId":  self.account_id,
            "from":       self.from_address,
            "to":         self.to_address,
            "token":      self.token.id,
            "fee":        self.fee,
            "nonce":      self.nonce,
            "signature":  self.signature.dict(),
            "amount":     self.amount,
            "validFrom":  self.valid_from,
            "validUntil": self.valid_until,
        }


@dataclass
class Withdraw(EncodedTx):
    account_id: int
    from_address: str
    to_address: str
    amount: int
    fee: int
    nonce: int
    valid_from: int
    valid_until: int
    token: Token
    signature: TxSignature = None

    def tx_type(self) -> int:
        return 3

    def human_readable_message(self) -> str:
        message = f"Withdraw {self.token.decimal_str_amount(self.amount)} {self.token.symbol} to: {self.to_address.lower()}\nFee: {self.token.decimal_str_amount(self.fee)} {self.token.symbol}\nNonce: {self.nonce}"
        return message

    def encoded_message(self) -> bytes:
        return b"".join([
            int_to_bytes(self.tx_type(), 1),
            serialize_account_id(self.account_id),
            serialize_address(self.from_address),
            serialize_address(self.to_address),
            serialize_token_id(self.token.id),
            int_to_bytes(self.amount, length=16),
            packed_fee_checked(self.fee),
            serialize_nonce(self.nonce),
            serialize_timestamp(self.valid_from),
            serialize_timestamp(self.valid_until)
        ])

    def dict(self):
        return {
            "type":       "Withdraw",
            "accountId":  self.account_id,
            "from":       self.from_address,
            "to":         self.to_address,
            "token":      self.token.id,
            "fee":        self.fee,
            "nonce":      self.nonce,
            "signature":  self.signature.dict(),
            "amount":     self.amount,
            "validFrom":  self.valid_from,
            "validUntil": self.valid_until,
        }


@dataclass
class ForcedExit(EncodedTx):
    initiator_account_id: int
    target: str
    token: Token
    fee: int
    nonce: int
    valid_from: int
    valid_until: int
    signature: TxSignature = None

    def tx_type(self) -> int:
        return 8

    def encoded_message(self) -> bytes:
        return b"".join([
            int_to_bytes(self.tx_type(), 1),
            serialize_account_id(self.initiator_account_id),
            serialize_address(self.target),
            serialize_token_id(self.token.id),
            packed_fee_checked(self.fee),
            serialize_nonce(self.nonce),
            serialize_timestamp(self.valid_from),
            serialize_timestamp(self.valid_until)
        ])

    def human_readable_message(self) -> str:
        message = f"ForcedExit {self.token.symbol} to: {self.target.lower()}\nFee: {self.token.decimal_str_amount(self.fee)} {self.token.symbol}\nNonce: {self.nonce}"
        return message

    def dict(self):
        return {
            "type":               "ForcedExit",
            "initiatorAccountId": self.initiator_account_id,
            "target":             self.target,
            "token":              self.token.id,
            "fee":                self.fee,
            "nonce":              self.nonce,
            "signature":          self.signature.dict(),
            "validFrom":          self.valid_from,
            "validUntil":         self.valid_until,
        }


class ContractAddress:
    main_contract: str
    gov_contract: str


@dataclass
class Tokens:
    tokens: List[Token]

    def __init__(self, tokens=None):
        self.tokens = tokens or []

    def find_by_address(self, address: str) -> Optional[Token]:
        found_token = [token for token in self.tokens if token.address == address]
        if found_token:
            return found_token[0]
        else:
            return None

    def find_by_id(self, token_id: int) -> Optional[Token]:
        found_token = [token for token in self.tokens if token.id == token_id]
        if found_token:
            return found_token[0]
        else:
            return None

    def find_by_symbol(self, symbol: str) -> Optional[Token]:
        found_token = [token for token in self.tokens if token.symbol == symbol]
        if found_token:
            return found_token[0]
        else:
            return None


@dataclass
class SignedTransaction:
    transaction: EncodedTx
    eth_signature: bytes
