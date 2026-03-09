from pydantic import BaseModel
from .user import User
from .vehicle import Vehicle



class Ride(BaseModel):
    ride_id: str
    user_id: str
    vehicle_id: str
    is_degraded_report: bool = False  # Track if the ride ended due to a breakdown

    def calculate_cost(self) -> int:
        """Returns the cost of the ride based on the business rules."""
        if self.is_degraded_report:
            return 0  # Free ride if reported degraded [cite: 100, 239]
        return 15  # Constant 15 ILS for a normal ride


# --- Inside FleetManager or API endpoint for ending a ride ---

def process_end_of_ride(user: User, ride: Ride):
    """Processes the end of a ride by calculating the cost, charging the user, and clearing the active ride."""

    # 1. The Ride calculates the cost (either 15 or 0)
    final_price = ride.calculate_cost()

    # 2. The User is charged that exact amount
    user.charge(final_price)

    # 3. Clear the user's active ride
    user.current_ride_id = None