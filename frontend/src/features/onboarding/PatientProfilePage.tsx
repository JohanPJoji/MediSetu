import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../../lib/api';
import { Button } from '../../components/primitives/Button';
import { Input } from '../../components/primitives/Input';
import { Select } from '../../components/primitives/Select';
import styles from './PatientProfilePage.module.css';

const SEX_OPTIONS = [
  { value: 'FEMALE', label: 'Female' },
  { value: 'MALE',   label: 'Male' },
  { value: 'OTHER',  label: 'Other / Prefer not to say' },
];

const LANGUAGE_OPTIONS = [
  { value: 'en', label: 'English' },
  { value: 'hi', label: 'हिन्दी (Hindi)' },
  { value: 'ml', label: 'മലയാളം (Malayalam)' },
  { value: 'ta', label: 'தமிழ் (Tamil)' },
  { value: 'te', label: 'తెలుగు (Telugu)' },
  { value: 'ar', label: 'العربية (Arabic)' },
  { value: 'bn', label: 'বাংলা (Bengali)' },
  { value: 'other', label: 'Other' },
];

export function PatientProfilePage() {
  const navigate = useNavigate();

  const [name,     setName]     = useState('');
  const [dob,      setDob]      = useState('');
  const [sex,      setSex]      = useState('FEMALE');
  const [contact,  setContact]  = useState('');
  const [language, setLanguage] = useState('en');
  const [error,    setError]    = useState('');
  const [saving,   setSaving]   = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setSaving(true);
    try {
      await api.createPatientProfile({
        name,
        date_of_birth: dob,
        sex: sex as 'MALE' | 'FEMALE' | 'OTHER',
        contact_information: contact,
        preferred_language: language,
      });
      navigate('/dashboard', { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not save your profile. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1 className={styles.title}>Complete your profile</h1>
        <p className={styles.subtitle}>
          We need a few details before you can start a consultation. Your information
          is kept private and used only for your care.
        </p>
      </div>

      <form onSubmit={submit} className={styles.form} noValidate>
        <Input
          id="patient-name"
          label="Full name"
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
          placeholder="As it appears on your ID"
        />

        <Input
          id="patient-dob"
          label="Date of birth"
          type="date"
          value={dob}
          onChange={(e) => setDob(e.target.value)}
          required
        />

        <Select
          id="patient-sex"
          label="Biological sex"
          options={SEX_OPTIONS}
          value={sex}
          onChange={(e) => setSex(e.target.value)}
          required
          hint="Used for medical calculations. You can discuss gender identity with your doctor."
        />

        <Input
          id="patient-contact"
          label="Phone number or email"
          type="text"
          value={contact}
          onChange={(e) => setContact(e.target.value)}
          required
          placeholder="+91 98765 43210"
          hint="Used only to contact you about your care."
        />

        <Select
          id="patient-language"
          label="Preferred language for consultations"
          options={LANGUAGE_OPTIONS}
          value={language}
          onChange={(e) => setLanguage(e.target.value)}
          hint="The AI assistant will use this language during your pre-consultation."
        />

        {error && (
          <div className={styles.errorBox} role="alert">
            {error}
          </div>
        )}

        <Button
          type="submit"
          variant="primary"
          size="lg"
          loading={saving}
          className={styles.submitBtn}
        >
          Save and continue
        </Button>
      </form>
    </div>
  );
}
