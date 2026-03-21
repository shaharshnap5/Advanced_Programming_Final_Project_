from pydantic import BaseModel, Field

class UserCreate(BaseModel):
    user_id: str = Field(..., min_length=1, description="User unique identifier")
    first_name: str = Field(..., min_length=1, description="User first name")
    last_name: str = Field(..., min_length=1, description="User last name")
    email: str = Field(..., min_length=3, description="User email address")

class User(BaseModel):
    user_id: str
    first_name: str
    last_name: str
    email: str
    payment_token: str

    def can_start_ride(self) -> bool:
        """User model is stateless regarding active rides."""

        return True

    def charge(self, amount: int):
        """Mocks the charging process using the stored payment token."""

        if not self.payment_token:
            raise ValueError("No payment token found for user.")

        # Here you would typically integrate with Stripe/PayPal as mentioned in your design.
        print(f"Charged user {self.user_id} {amount} ILS using token {self.payment_token}.")

class UserRegisterResponse(BaseModel):
    message: str = Field(..., description="Status message")
    user: User = Field(..., description="User details")

