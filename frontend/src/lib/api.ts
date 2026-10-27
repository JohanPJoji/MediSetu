export type Role="PATIENT"|"DOCTOR"|"NURSE"|"PHARMACY"|"ADMIN";
export interface ApiEnvelope<T>{success:boolean;data:T;message:string|null}
const TOKEN_KEY="medisetu.access_token";
export const auth={getToken:()=>localStorage.getItem(TOKEN_KEY),setToken:(t:string)=>localStorage.setItem(TOKEN_KEY,t),clear:()=>localStorage.removeItem(TOKEN_KEY)};
async function request<T>(path:string,init:RequestInit={}):Promise<T>{const headers=new Headers(init.headers);if(init.body&&!(init.body instanceof FormData))headers.set("Content-Type","application/json");const token=auth.getToken();if(token)headers.set("Authorization",`Bearer ${token}`);const r=await fetch(path,{...init,headers});const p=await r.json().catch(()=>null);if(!r.ok)throw new Error(p?.error?.message??p?.detail??`Request failed (${r.status})`);return p as T;}
const get=<T>(path:string)=>request<ApiEnvelope<T>>(path); const post=<T>(path:string,body:unknown)=>request<ApiEnvelope<T>>(path,{method:"POST",body:JSON.stringify(body)});
 export const api={
  login:(email:string,password:string)=>post<{access_token:string;token_type:string}>("/api/auth/login",{email,password}),
  register:(email:string,password:string,full_name:string)=>post<unknown>("/api/auth/register",{email,password,full_name,role:"PATIENT"}),
  me:()=>get<{id:string;email:string;full_name:string;role:Role}>("/api/users/me"),
  patientMe:()=>get<any>("/api/patients/me"),
  createPatientProfile:(body:{name:string;date_of_birth:string;sex:"MALE"|"FEMALE"|"OTHER";contact_information:string;preferred_language?:string})=>post<any>("/api/patients",body),
  consultations:()=>get<any[]>("/api/consultations"),
  consultation:(id:string)=>get<any>(`/api/consultations/${id}`),
  createConsultation:(patient_id:string)=>post<any>("/api/consultations",{patient_id}), 
  updateConsultationStatus:(id:string,status:string)=>request<ApiEnvelope<any>>(`/api/consultations/${id}/status`,{method:"PATCH",body:JSON.stringify({status})}),
  completeConsultation:(id:string)=>post<any>(`/api/consultations/${id}/complete`,{}),
  transcript:(id:string)=>get<any[]>(`/api/consultations/${id}/transcript`),
  addTranscript:(id:string,content:string)=>post<any>(`/api/consultations/${id}/transcript`,{role:"PATIENT",content,language:"en"}),
  processIntake:(id:string)=>request<ApiEnvelope<any>>(`/api/consultations/${id}/process-intake`,{method:"POST"}), 
  clinicalHistory:(id:string)=>get<any>(`/api/consultations/${id}/clinical-history`),
  voiceInput:(id:string,blob:Blob)=>{const form=new FormData();form.append("audio",blob,"recording.webm");return request<ApiEnvelope<any>>(`/api/consultations/${id}/voice-input`,{method:"POST",body:form})},
  followUp:(id:string)=>request<ApiEnvelope<any>>(`/api/consultations/${id}/follow-up`,{method:"POST"}),
  summary:(id:string)=>get<any>(`/api/consultations/${id}/summary`),
  aiSuggestions:(id:string)=>request<ApiEnvelope<any>>(`/api/consultations/${id}/ai-suggestions`,{method:"POST"}),
  medicineSuggestions:(id:string)=>get<any[]>(`/api/consultations/${id}/medicine-suggestions`),
  medicines:()=>get<any[]>("/api/medicines"), 
  prescriptions:()=>get<any[]>("/api/prescriptions"), 
  dispensePrescription:(id:string)=>post<any>(`/api/prescriptions/${id}/dispense`,{}),
  referrals:()=>get<any[]>("/api/referrals"), 
  createReferral:(consultation_id:string,referred_to_specialty:string,reason:string,priority:string)=>post<any>("/api/referrals",{consultation_id,referred_to_specialty,reason,priority}),
  pharmacyOrders:()=>get<any[]>("/api/pharmacy/orders"),
  labTests:()=>get<any[]>("/api/laboratory/tests"), 
  labOrders:()=>get<any[]>("/api/laboratory/orders"), 
  orderLabTest:(consultation_id:string,test_name:string)=>post<any>("/api/laboratory/orders",{consultation_id,test_name}),
  bills:()=>get<any[]>("/api/billing"), 
  inventory:()=>get<any[]>("/api/inventory"),
  inventoryBatches:()=>get<any[]>("/api/inventory/batches"), 
  alerts:()=>get<any[]>("/api/alerts/medicine-alerts")
};
