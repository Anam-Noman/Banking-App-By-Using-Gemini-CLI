from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# In-memory user database
users: Dict[str, Dict] = {
    "Ali": {"pin": 1234, "bank_balance": 10000.0},
    "Sara": {"pin": 4321, "bank_balance": 15000.0}
}

# ========================
# Pydantic Models for Request Bodies
# ========================

class DepositRequest(BaseModel):
    name: str
    amount_to_deposit: float

class AuthenticateRequest(BaseModel):
    name: str
    pin_number: int

class BankTransferRequest(BaseModel):
    sender_name: str
    sender_pin: int
    recipients_name: str
    amount_to_transfer: float

class UserDetailsResponse(BaseModel):
    name: str
    pin: int
    bank_balance: float

# ========================
# Helper Functions
# ========================

def _authenticate_user(name: str, pin: int) -> bool:
    """Checks if a user exists and the PIN is correct."""
    user = users.get(name)
    if user and user["pin"] == pin:
        return True
    return False

# ========================
# GET ALL USERS ENDPOINT
# ========================

@app.get("/users", response_model=Dict[str, Dict])
def get_users():
    """
    Retrieves and returns all user data from the in-memory database.
    """
    return users


# ========================
# DEPOSIT ENDPOINT
# ========================

@app.post("/deposit", response_model=UserDetailsResponse)
def deposit(request: DepositRequest):
    """
    Deposits a given amount into a user's account.
    """
    user = users.get(request.name)
    if not user:
        raise HTTPException(status_code=404, detail=f"User '{request.name}' not found.")

    if request.amount_to_deposit <= 0:
        raise HTTPException(status_code=400, detail="Deposit amount must be positive.")

    user["bank_balance"] += request.amount_to_deposit
    
    return {"name": request.name, **user}


# ========================
# AUTHENTICATE ENDPOINT
# ========================

@app.post("/authenticate", response_model=UserDetailsResponse)
def authenticate(request: AuthenticateRequest):
    """
    Authenticates a user with their name and PIN.
    Returns user details if successful.
    """
    if _authenticate_user(request.name, request.pin_number):
        user_details = users[request.name]
        return {"name": request.name, **user_details}
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")


# ========================
# BANK TRANSFER ENDPOINT
# ========================

@app.post("/bank-transfer", response_model=UserDetailsResponse)
def bank_transfer(request: BankTransferRequest):
    """
    Transfers an amount from a sender to a recipient.
    1. Authenticates sender.
    2. Checks for sufficient funds.
    3. Performs the transfer.
    4. Returns the updated details of the recipient.
    """
    # 1. Authenticate sender
    if not _authenticate_user(request.sender_name, request.sender_pin):
        raise HTTPException(status_code=401, detail="Invalid sender credentials.")

    sender = users.get(request.sender_name)
    recipient = users.get(request.recipients_name)

    # Basic validations
    if not recipient:
        raise HTTPException(status_code=404, detail=f"Recipient '{request.recipients_name}' not found.")
    
    if request.sender_name == request.recipients_name:
        raise HTTPException(status_code=400, detail="Sender and recipient cannot be the same person.")

    if request.amount_to_transfer <= 0:
        raise HTTPException(status_code=400, detail="Transfer amount must be positive.")

    # 2. Check for sufficient funds
    if sender["bank_balance"] < request.amount_to_transfer:
        raise HTTPException(status_code=400, detail="Insufficient funds for transfer.")

    # 3. Perform transfer
    sender["bank_balance"] -= request.amount_to_transfer
    recipient["bank_balance"] += request.amount_to_transfer

    # 4. Return updated recipient details
    return {"name": request.recipients_name, **recipient}
