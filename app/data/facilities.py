"""
app/data/facilities.py — Agent O (Round 3): static facility directory.

Deliberately simple, per the work order: no geolocation / nearest-facility
matching, just a small seed list the caller (frontend, or whoever creates
a referral) picks from.

SEED DATA NOTE: the names, cities, and contact numbers below are
placeholder demo entries for the hackathon build, not a verified list of
real partner facilities. Swap in your actual referral network's real,
verified contact details before this is anywhere near a real patient.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Facility:
    id: str
    name: str
    city: str
    contact: str


FACILITIES: list[Facility] = [
    Facility("fac-01", "City Eye Care Centre", "Mumbai", "+91-22-4550-1010"),
    Facility("fac-02", "Regional Retina & Eye Institute", "Pune", "+91-20-4551-2020"),
    Facility("fac-03", "Sunrise Eye Hospital", "Bengaluru", "+91-80-4552-3030"),
    Facility("fac-04", "Netra Jyoti Eye Care", "Delhi", "+91-11-4553-4040"),
    Facility("fac-05", "Lotus Ophthalmology Centre", "Chennai", "+91-44-4554-5050"),
    Facility("fac-06", "Vision Plus Eye Hospital", "Hyderabad", "+91-40-4555-6060"),
    Facility("fac-07", "Kolkata Eye Research Centre", "Kolkata", "+91-33-4556-7070"),
    Facility("fac-08", "Green Valley Eye Institute", "Ahmedabad", "+91-79-4557-8080"),
    Facility("fac-09", "Sadbhavna Netra Chikitsalaya", "Lucknow", "+91-522-4558-9090"),
    Facility("fac-10", "Coastal Vision & Eye Care", "Kochi", "+91-484-4559-0101"),
]
