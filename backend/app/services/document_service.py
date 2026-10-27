from uuid import UUID
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.document import Document
from app.schemas.document import DocumentCreate
from app.services.audit_service import record_audit_event

async def create_document(db: AsyncSession, document_in: DocumentCreate) -> Document:
    db_document = Document(
        patient_id=document_in.patient_id,
        consultation_id=document_in.consultation_id,
        file_name=document_in.file_name,
        file_type=document_in.file_type,
        file_url=document_in.file_url,
        extracted_text=document_in.extracted_text
    )
    db.add(db_document)
    await db.commit()
    await db.refresh(db_document)
    await record_audit_event(
        db, action="DOCUMENT_UPLOADED", resource_type="Document",
        resource_id=db_document.id, metadata={"patient_id": str(db_document.patient_id)}
    )
    await db.commit()
    return db_document

async def list_documents(db: AsyncSession, patient_id: Optional[UUID] = None) -> List[Document]:
    query = select(Document)
    if patient_id:
        query = query.where(Document.patient_id == patient_id)
        
    result = await db.execute(query)
    return list(result.scalars().all())

async def get_document(db: AsyncSession, document_id: UUID) -> Optional[Document]:
    result = await db.execute(select(Document).where(Document.id == document_id))
    return result.scalars().first()


async def list_documents_for_doctor(db: AsyncSession, doctor_id: UUID) -> List[Document]:
    from app.models.consultation import Consultation
    query = (
        select(Document)
        .join(Consultation, Document.consultation_id == Consultation.id)
        .where(Consultation.doctor_id == doctor_id)
        .order_by(Document.created_at.desc())
    )
    result = await db.execute(query)
    return list(result.scalars().all())
