from pydantic import BaseModel
from typing import Optional


class User(BaseModel):
    user_id: str
    payment_token: str
    current_ride_id: Optional[str] = None


    def can_start_ride(self) -> bool:
        """Checks if the user is allowed to start a new ride."""

        return self.current_ride_id is None


    def charge(self, amount: int):
        """Mocks the charging process using the stored payment token."""

        if not self.payment_token:
            raise ValueError("No payment token found for user.")

        # Here you would typically integrate with Stripe/PayPal as mentioned in your design.
        print(f"Charged user {self.user_id} {amount} ILS using token {self.payment_token}.")
