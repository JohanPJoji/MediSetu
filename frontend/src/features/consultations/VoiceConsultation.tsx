import { useEffect, useRef, useState, type FormEvent } from 'react';
import { Microphone, Stop, Warning, Info, CheckCircle } from '@phosphor-icons/react';
import { api } from '../../lib/api';
import { Button } from '../../components/primitives/Button';
import { Input } from '../../components/primitives/Input';
import { StatusBadge } from '../../components/primitives/Badge';
import { TranscriptPanel } from './TranscriptPanel';
import type { TranscriptTurn } from './TranscriptPanel';
import styles from './VoiceConsultation.module.css';

type VoiceState = 'idle' | 'recording' | 'processing' | 'error' | 'finished';

interface VoiceConsultationProps {
  consultationId: string;
  onUpdated: () => void;
}

export function VoiceConsultation({ consultationId, onUpdated }: VoiceConsultationProps) {
  const [turns, setTurns]             = useState<TranscriptTurn[]>([]);
  const [question, setQuestion]       = useState<string | null>(null);
  const [voiceState, setVoiceState]   = useState<VoiceState>('idle');
  const [voiceError, setVoiceError]   = useState('');
  const [emergency, setEmergency]     = useState<string | null>(null);
  const [lastTranscript, setLastTranscript] = useState('');
  const [lowConfidence, setLowConfidence]   = useState(false);
  const [showTyping, setShowTyping]   = useState(false);
  const [typedText, setTypedText]     = useState('');
  const [intakeComplete, setIntakeComplete] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  // Continuous conversation state
  const [isContinuousMode, setIsContinuousMode] = useState(false);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef        = useRef<Blob[]>([]);
  
  // VAD refs
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const vadStateRef = useRef<'waiting' | 'speaking' | 'silence'>('waiting');
  const silenceStartRef = useRef<number>(0);
  const rafRef = useRef<number>(0);
  
  const audioSupported   = Boolean(navigator.mediaDevices?.getUserMedia);

  const loadTranscript = async () => {
    try {
      const r = await api.transcript(consultationId);
      setTurns(r.data as TranscriptTurn[]);
    } catch { /* silently ignore */ }
  };

  useEffect(() => { loadTranscript(); }, [consultationId]);

  // Clean up VAD and MediaRecorder on unmount
  useEffect(() => {
    return () => {
      cancelAnimationFrame(rafRef.current);
      if (audioContextRef.current?.state !== 'closed') {
        audioContextRef.current?.close();
      }
      mediaRecorderRef.current?.stop();
    };
  }, []);

  const applyResult = (data: Record<string, unknown>) => {
    setLastTranscript(String(data.transcript ?? ''));
    setLowConfidence(Boolean(data.low_confidence_retry));
    
    if (data.is_emergency) {
      setEmergency(String(data.emergency_instructions ?? data.assistant_message ?? 'Please seek immediate medical attention.'));
      setQuestion(null);
      setIsContinuousMode(false); // Stop continuous mode on emergency
    } else {
      setEmergency(null);
      const q = (data.follow_up_questions as string[])?.[0] ?? data.assistant_message ?? null;
      setQuestion(q ? String(q) : null);
    }
    
    const complete = Boolean(data.intake_complete);
    setIntakeComplete(complete);
    
    loadTranscript();
    onUpdated();

    if (data.audio_response_url) {
      const audio = new Audio(String(data.audio_response_url));
      audio.onended = () => {
        if (!complete && !data.is_emergency && isContinuousMode) {
          startRecording();
        }
      };
      audio.play().catch(() => {
        // If autoplay blocked, fallback to delay
        if (!complete && !data.is_emergency && isContinuousMode) {
          setTimeout(startRecording, 2000);
        }
      });
    } else {
      // If no audio returned, wait briefly then resume
      if (!complete && !data.is_emergency && isContinuousMode) {
        setTimeout(startRecording, 2000);
      }
    }
  };

  const startVAD = (stream: MediaStream) => {
    const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
    audioContextRef.current = audioCtx;
    const source = audioCtx.createMediaStreamSource(stream);
    const analyser = audioCtx.createAnalyser();
    analyser.fftSize = 256;
    analyser.smoothingTimeConstant = 0.4;
    source.connect(analyser);
    analyserRef.current = analyser;
    
    vadStateRef.current = 'waiting';
    silenceStartRef.current = 0;
    
    const dataArray = new Uint8Array(analyser.frequencyBinCount);
    
    const checkVolume = () => {
      if (mediaRecorderRef.current?.state !== 'recording') return;
      
      analyser.getByteFrequencyData(dataArray);
      let sum = 0;
      for (let i = 0; i < dataArray.length; i++) {
        sum += dataArray[i];
      }
      const average = sum / dataArray.length;
      
      const THRESHOLD = 10; // Adjust as needed
      const SILENCE_DURATION_MS = 2000; // 2 seconds of silence
      
      if (average > THRESHOLD) {
        if (vadStateRef.current !== 'speaking') {
          vadStateRef.current = 'speaking';
        }
      } else {
        if (vadStateRef.current === 'speaking') {
          vadStateRef.current = 'silence';
          silenceStartRef.current = performance.now();
        } else if (vadStateRef.current === 'silence') {
          if (performance.now() - silenceStartRef.current > SILENCE_DURATION_MS) {
            // Stop recording
            stopRecording();
            return;
          }
        }
      }
      
      rafRef.current = requestAnimationFrame(checkVolume);
    };
    
    checkVolume();
  };

  const startRecording = async () => {
    setVoiceError('');
    if (!audioSupported) {
      setVoiceState('error');
      setVoiceError('Microphone recording is not available in this browser. Please type your answer below.');
      setShowTyping(true);
      return;
    }
    
    setIsContinuousMode(true);
    
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      chunksRef.current = [];
      recorder.ondataavailable = (e) => { if (e.data.size > 0) chunksRef.current.push(e.data); };
      recorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        cancelAnimationFrame(rafRef.current);
        if (audioContextRef.current?.state !== 'closed') {
          audioContextRef.current?.close();
        }
        
        setVoiceState('processing');
        try {
          const blob   = new Blob(chunksRef.current, { type: 'audio/webm' });
          const result = await api.voiceInput(consultationId, blob);
          applyResult(result.data as Record<string, unknown>);
          setVoiceState('idle');
        } catch (err) {
          setVoiceState('error');
          setVoiceError(err instanceof Error ? err.message : 'Voice processing failed. Please try again or type your answer below.');
          setShowTyping(true);
          setIsContinuousMode(false);
        }
      };
      
      recorder.start(250); // timeslice for continuous VAD buffer if needed
      mediaRecorderRef.current = recorder;
      setVoiceState('recording');
      
      startVAD(stream);
    } catch {
      setVoiceState('error');
      setVoiceError('Microphone permission denied. Please allow access in your browser, or type your answer below.');
      setShowTyping(true);
      setIsContinuousMode(false);
    }
  };

  const stopRecording = () => {
    mediaRecorderRef.current?.stop();
    mediaRecorderRef.current = null;
  };

  const stopContinuousMode = () => {
    setIsContinuousMode(false);
    stopRecording();
  };

  const submitTyped = async (e: FormEvent) => {
    e.preventDefault();
    if (!typedText.trim()) return;
    setVoiceState('processing');
    setVoiceError('');
    setIsContinuousMode(false); // Typing breaks continuous voice mode
    try {
      const added = await api.addTranscript(consultationId, typedText);
      setTypedText('');
      const data = added.data as Record<string, unknown>;
      
      if (data.is_emergency) {
        setEmergency(String(data.emergency_instructions ?? 'Please seek immediate medical attention.'));
        setQuestion(null);
        await loadTranscript();
      } else {
        setEmergency(null);
        const follow = await api.followUp(consultationId);
        const fd = follow.data as Record<string, unknown>;
        setQuestion(fd.question ? String(fd.question) : null);
        setIntakeComplete(Boolean(fd.intake_complete));
        await loadTranscript();
      }
      onUpdated();
      setVoiceState('idle');
    } catch (err) {
      setVoiceState('error');
      setVoiceError(err instanceof Error ? err.message : 'Could not send your answer. Please try again.');
    }
  };

  const sendToDoctor = async () => {
    setIsSubmitting(true);
    setVoiceError('');
    try {
      // Process intake data (summarize/structure)
      await api.processIntake(consultationId);
      // Change status to IN_PROGRESS to move it to doctor's queue
      await api.updateConsultationStatus(consultationId, 'IN_PROGRESS');
      setVoiceState('finished');
      onUpdated(); // This will unmount this component as ConsultationDetailPage changes state
    } catch (err) {
      setVoiceError(err instanceof Error ? err.message : 'Failed to send to doctor. Please try again.');
      setIsSubmitting(false);
    }
  };

  if (voiceState === 'finished') {
    return (
      <div className={styles.wrapper}>
        <div className={styles.successMessage}>
          <CheckCircle size={48} weight="fill" color="var(--color-success)" />
          <h3>Consultation Details Sent</h3>
          <p>The doctor will review your information shortly.</p>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.wrapper}>
      {/* AI disclosure — always visible, non-negotiable per design.md */}
      <div className={styles.disclosure} role="note">
        <Info size={16} aria-hidden="true" />
        <span>
          You're speaking with an AI assistant. A doctor will review all your answers
          before any medical decision is made.
        </span>
      </div>

      {/* Emergency banner — StatusBadge pattern (icon + label + color) */}
      {emergency && (
        <div className={styles.emergencyBanner} role="alert">
          <StatusBadge severity="critical" label="Emergency" />
          <p className={styles.emergencyText}>{emergency}</p>
        </div>
      )}

      {/* Current AI question */}
      <div className={styles.questionBox}>
        <span className={styles.questionLabel}>Current question</span>
        <p className={styles.questionText}>
          {question ?? 'Please describe your symptoms or what brought you in today.'}
        </p>
      </div>

      {/* Control Area */}
      <div className={styles.micArea}>
        {intakeComplete ? (
          <div className={styles.completeActions}>
            <p className={styles.statusText}>I have all the details I need. You can now send this to the doctor.</p>
            <Button
              variant="primary"
              size="lg"
              icon={<CheckCircle size={20} weight="fill" />}
              onClick={sendToDoctor}
              disabled={isSubmitting}
              loading={isSubmitting}
              className={styles.micBtn}
            >
              Confirm & Send to Doctor
            </Button>
          </div>
        ) : (
          <>
            {voiceState === 'recording' || isContinuousMode ? (
              <Button
                variant="destructive"
                size="lg"
                icon={<Stop size={20} weight="fill" />}
                onClick={stopContinuousMode}
                className={styles.micBtn}
              >
                Stop Conversation
              </Button>
            ) : (
              <Button
                variant="primary"
                size="lg"
                icon={<Microphone size={20} weight="fill" />}
                onClick={startRecording}
                disabled={voiceState === 'processing'}
                loading={voiceState === 'processing'}
                className={styles.micBtn}
              >
                {voiceState === 'processing' ? 'Processing…' : 'Start Conversation'}
              </Button>
            )}

            {voiceState === 'recording' && (
              <p className={styles.statusText}>Listening… will pause automatically when you stop speaking.</p>
            )}
            {voiceState === 'processing' && isContinuousMode && (
              <p className={styles.statusText}>Thinking…</p>
            )}
            {voiceState === 'idle' && isContinuousMode && !intakeComplete && (
              <p className={styles.statusText}>Waiting for assistant response…</p>
            )}
            {voiceState === 'idle' && !isContinuousMode && lastTranscript && (
              <p className={styles.statusText}>You said: "{lastTranscript}"</p>
            )}
            {lowConfidence && (
              <p className={styles.statusText}>That wasn't very clear — please try again.</p>
            )}
            {voiceState === 'error' && voiceError && (
              <div className={styles.errorBox} role="alert">{voiceError}</div>
            )}
          </>
        )}
      </div>

      {/* Typing fallback */}
      {!intakeComplete && (
        <div className={styles.typingSection}>
          <button
            type="button"
            className={styles.typingToggle}
            onClick={() => {
              setShowTyping((s) => !s);
              if (!showTyping) stopContinuousMode();
            }}
            aria-expanded={showTyping}
          >
            {showTyping ? 'Hide text input' : 'Type your answer instead'}
          </button>
          {showTyping && (
            <form onSubmit={submitTyped} className={styles.typingForm}>
              <Input
                id="typed-answer"
                label="Your answer"
                value={typedText}
                onChange={(e) => setTypedText(e.target.value)}
                placeholder="Type here…"
              />
              <Button type="submit" variant="secondary" disabled={voiceState === 'processing'}>
                Send
              </Button>
            </form>
          )}
        </div>
      )}

      {/* Transcript */}
      <div className={styles.transcriptArea}>
        <TranscriptPanel turns={turns} />
      </div>
    </div>
  );
}
