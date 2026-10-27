from typing import List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.transcript import TranscriptEntry
from app.schemas.transcript import TranscriptEntryCreate
from app.services.audit_service import record_audit_event

async def create_transcript_entry(db: AsyncSession, consultation_id: UUID, entry_in: TranscriptEntryCreate) -> TranscriptEntry:
    db_entry = TranscriptEntry(
        consultation_id=consultation_id,
        role=entry_in.role,
        content=entry_in.content,
        language=entry_in.language
    )
    db.add(db_entry)
    await db.commit()
    await db.refresh(db_entry)
    await record_audit_event(
        db, action="TRANSCRIPT_ENTRY_ADDED", resource_type="Consultation",
        resource_id=consultation_id, metadata={"role": entry_in.role.value}
    )
    await db.commit()
    return db_entry

async def list_transcript_entries(db: AsyncSession, consultation_id: UUID) -> List[TranscriptEntry]:
    result = await db.execute(
        select(TranscriptEntry)
        .where(TranscriptEntry.consultation_id == consultation_id)
        .order_by(TranscriptEntry.created_at)
    )
    return list(result.scalars().all())
