from typing import Dict, Any
from uuid import UUID

class ABHAService:
    async def verify_abha_address(self, abha_address: str) -> bool:
        # Mock implementation
        return abha_address.endswith("@abdm")
        
    async def get_patient_profile(self, abha_address: str) -> Dict[str, Any]:
        # Mock implementation
        if not await self.verify_abha_address(abha_address):
            raise ValueError("Invalid ABHA Address")
        return {
            "name": "Mock Patient",
            "gender": "M",
            "yearOfBirth": "1990",
            "mobile": "9999999999"
        }

class HISService:
    async def sync_patient(self, patient_data: Dict[str, Any]) -> bool:
        # Mock implementation: pretend we sync'd with the hospital HIS
        return True

    async def sync_consultation(self, consultation_data: Dict[str, Any]) -> bool:
        # Mock implementation
        return True

class FHIRMapper:
    @staticmethod
    def map_consultation_to_fhir(consultation_id: UUID, clinical_history: Dict[str, Any]) -> Dict[str, Any]:
        # Very simplified mock FHIR Encounter/Condition resource
        return {
            "resourceType": "Encounter",
            "id": str(consultation_id),
            "status": "finished",
            "subject": {
                "reference": "Patient/MockPatientID"
            },
            "reasonCode": [
                {
                    "text": clinical_history.get("chief_complaint", "Unknown")
                }
            ]
        }

abha_service = ABHAService()
his_service = HISService()
fhir_mapper = FHIRMapper()
