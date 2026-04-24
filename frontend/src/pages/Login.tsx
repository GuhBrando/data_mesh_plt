import React, { useState, useRef, useLayoutEffect } from 'react'
import { Navigate, useNavigate, useSearchParams } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Loader2 } from 'lucide-react'
import { post, get } from '../lib/api'
import { setTokens, isSafeRedirect, decodeJwtPayload } from '../lib/auth'
import { useAuth } from '../contexts/AuthContext'
import type { User } from '../types'

// ─── Schemas ─────────────────────────────────────────────────────────────────

const signInSchema = z.object({
  email: z.string().email('Enter a valid email'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
})

const registerSchema = z
  .object({
    username: z.string().min(2, 'Username must be at least 2 characters'),
    email: z.string().email('Enter a valid email'),
    password: z.string().min(8, 'Password must be at least 8 characters'),
    confirmPassword: z.string(),
  })
  .refine((d) => d.password === d.confirmPassword, {
    message: 'Passwords do not match',
    path: ['confirmPassword'],
  })

type SignInValues = z.infer<typeof signInSchema>
type RegisterValues = z.infer<typeof registerSchema>

// ─── Helpers ─────────────────────────────────────────────────────────────────

interface LoginApiResponse {
  access_token: string
  refresh_token: string
}

async function performLogin(email: string, password: string): Promise<User> {
  const { access_token, refresh_token } = await post<LoginApiResponse>(
    '/auth/login',
    { email, password },
  )
  setTokens(access_token, refresh_token)
  const { sub } = decodeJwtPayload(access_token)
  return get<User>(`/users/${sub}`)
}

// ─── Sub-components ───────────────────────────────────────────────────────────

const GlassInput = React.forwardRef<
  HTMLInputElement,
  React.InputHTMLAttributes<HTMLInputElement> & { hasError?: boolean }
>(({ hasError, className, ...props }, ref) => (
  <input
    ref={ref}
    {...props}
    className={`w-full bg-transparent outline-none text-sm text-white ${className ?? ''}`}
    style={{
      padding: '10px 14px',
      border: hasError
        ? '1px solid rgba(239,68,68,0.5)'
        : '1px solid rgba(255,255,255,0.1)',
      borderRadius: '10px',
      background: 'rgba(255,255,255,0.07)',
    }}
  />
))
GlassInput.displayName = 'GlassInput'

function GlassField({
  label,
  htmlFor,
  error,
  children,
}: {
  label: string
  htmlFor: string
  error?: string
  children: React.ReactNode
}) {
  return (
    <div className="mb-4">
      <label
        htmlFor={htmlFor}
        className="block text-xs font-medium mb-1.5"
        style={{ color: 'rgba(255,255,255,0.6)' }}
      >
        {label}
      </label>
      {children}
      {error && (
        <p className="mt-1 text-xs" style={{ color: '#f87171' }}>
          {error}
        </p>
      )}
    </div>
  )
}

function GlassButton({
  children,
  loading,
}: {
  children: React.ReactNode
  loading: boolean
}) {
  return (
    <button
      type="submit"
      disabled={loading}
      className="w-full flex items-center justify-center gap-2 py-2.5 mt-2 text-sm font-semibold text-white transition-opacity disabled:opacity-70"
      style={{
        background: 'linear-gradient(135deg, #6366f1, #a855f7)',
        borderRadius: '10px',
        border: 'none',
        cursor: loading ? 'not-allowed' : 'pointer',
      }}
    >
      {loading && <Loader2 size={15} className="animate-spin" />}
      {children}
    </button>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function Login() {
  const [mode, setMode] = useState<'signin' | 'register'>('signin')
  const [error, setError] = useState<string | null>(null)
  const { user, isLoading, setUser } = useAuth()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()

  const signInForm = useForm<SignInValues>({ resolver: zodResolver(signInSchema) })
  const registerForm = useForm<RegisterValues>({ resolver: zodResolver(registerSchema) })

  // Ref to the dynamic content area — used to animate height when mode changes
  const formContainerRef = useRef<HTMLDivElement>(null)

  // After mode changes, animate the container from its locked height to the new content height
  useLayoutEffect(() => {
    const el = formContainerRef.current
    if (!el || !el.style.height) return

    const lockedHeight = el.style.height

    requestAnimationFrame(() => {
      const target = formContainerRef.current
      if (!target) return

      // Measure true content height without the container constraint
      target.style.height = 'auto'
      const targetHeight = `${target.scrollHeight}px`

      // Restore locked height and flush layout — this becomes the transition's start value
      target.style.height = lockedHeight
      target.getBoundingClientRect()

      // Setting to target now triggers the CSS transition
      target.style.height = targetHeight
    })
  }, [mode])

  // Already authenticated — skip the login page
  if (!isLoading && user) return <Navigate to="/dashboard" replace />

  const rawRedirect = searchParams.get('redirect') ?? ''
  const redirectTo = isSafeRedirect(rawRedirect) ? rawRedirect : '/dashboard'

  function switchMode(next: 'signin' | 'register') {
    // Lock current height before content changes so the transition has a start value
    const el = formContainerRef.current
    if (el) el.style.height = `${el.scrollHeight}px`
    setMode(next)
    setError(null)
    signInForm.reset()
    registerForm.reset()
  }

  async function handleSignIn(values: SignInValues) {
    setError(null)
    try {
      const fetched = await performLogin(values.email, values.password)
      setUser(fetched)
      navigate(redirectTo, { replace: true })
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Something went wrong. Please try again.')
    }
  }

  async function handleRegister(values: RegisterValues) {
    setError(null)
    try {
      await post('/users', {
        username: values.username,
        email: values.email,
        password: values.password,
      })
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Registration failed. Please try again.')
      return
    }
    try {
      const fetched = await performLogin(values.email, values.password)
      setUser(fetched)
      navigate(redirectTo, { replace: true })
    } catch {
      switchMode('signin')
      setError('Account created. Please sign in to continue.')
    }
  }

  return (
    <div
      className="min-h-screen flex items-center justify-center relative overflow-hidden"
      style={{
        background: 'linear-gradient(135deg, #0d0d1a 0%, #1a0a2e 40%, #0d1a2e 100%)',
      }}
    >
      {/* Glow orbs */}
      <div
        className="absolute pointer-events-none"
        style={{
          top: '-100px',
          right: '-80px',
          width: '400px',
          height: '400px',
          borderRadius: '50%',
          background:
            'radial-gradient(circle, rgba(99,102,241,0.25) 0%, transparent 70%)',
        }}
      />
      <div
        className="absolute pointer-events-none"
        style={{
          bottom: '-60px',
          left: '-60px',
          width: '300px',
          height: '300px',
          borderRadius: '50%',
          background:
            'radial-gradient(circle, rgba(168,85,247,0.15) 0%, transparent 70%)',
        }}
      />

      {/* Glass card */}
      <div
        className="relative z-10 w-full mx-4"
        style={{
          maxWidth: '400px',
          background: 'rgba(255,255,255,0.05)',
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          border: '1px solid rgba(255,255,255,0.1)',
          borderRadius: '20px',
          padding: '40px 36px',
        }}
      >
        {/* Logo row */}
        <div className="flex items-center gap-3 mb-8">
          <div
            className="shrink-0"
            style={{
              width: '32px',
              height: '32px',
              background: 'linear-gradient(135deg, #6366f1, #a855f7)',
              borderRadius: '8px',
            }}
          />
          <span className="text-white font-bold text-lg tracking-tight">
            DataMesh
          </span>
        </div>

        {/* Pill toggle — sliding indicator moves left/right on click */}
        <div
          className="flex mb-7"
          style={{
            position: 'relative',
            background: 'rgba(255,255,255,0.06)',
            border: '1px solid rgba(255,255,255,0.1)',
            borderRadius: '999px',
            padding: '3px',
          }}
        >
          {/* Sliding active pill */}
          <div
            aria-hidden="true"
            style={{
              position: 'absolute',
              top: '3px',
              bottom: '3px',
              left: '3px',
              width: 'calc(50% - 3px)',
              background: 'linear-gradient(135deg, #6366f1, #a855f7)',
              borderRadius: '999px',
              transform: mode === 'signin' ? 'translateX(0)' : 'translateX(100%)',
              transition: 'transform 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
            }}
          />
          {(['signin', 'register'] as const).map((m) => (
            <button
              key={m}
              type="button"
              onClick={() => switchMode(m)}
              className="flex-1 py-2 text-sm font-semibold"
              style={{
                position: 'relative',
                zIndex: 1,
                borderRadius: '999px',
                border: 'none',
                cursor: 'pointer',
                background: 'transparent',
                color: mode === m ? '#fff' : 'rgba(255,255,255,0.4)',
                transition: 'color 0.25s ease',
              }}
            >
              {m === 'signin' ? 'Sign In' : 'Register'}
            </button>
          ))}
        </div>

        {/* Dynamic area — height animates smoothly when switching modes */}
        <div
          ref={formContainerRef}
          style={{ overflow: 'hidden', transition: 'height 0.3s ease' }}
        >
          {/* Error banner */}
          {error && (
            <div
              className="mb-5 text-sm"
              style={{
                background: 'rgba(239,68,68,0.15)',
                border: '1px solid rgba(239,68,68,0.3)',
                borderRadius: '10px',
                padding: '12px 14px',
                color: '#fca5a5',
              }}
            >
              {error}
            </div>
          )}

          {/* Sign In form */}
          {mode === 'signin' && (
            <form onSubmit={signInForm.handleSubmit(handleSignIn)} noValidate>
              <GlassField
                label="Email"
                htmlFor="signin-email"
                error={signInForm.formState.errors.email?.message}
              >
                <GlassInput
                  {...signInForm.register('email')}
                  id="signin-email"
                  type="email"
                  placeholder="you@company.com"
                  autoComplete="email"
                  hasError={!!signInForm.formState.errors.email}
                />
              </GlassField>
              <GlassField
                label="Password"
                htmlFor="signin-password"
                error={signInForm.formState.errors.password?.message}
              >
                <GlassInput
                  {...signInForm.register('password')}
                  id="signin-password"
                  type="password"
                  placeholder="••••••••"
                  autoComplete="current-password"
                  hasError={!!signInForm.formState.errors.password}
                />
              </GlassField>
              <GlassButton loading={signInForm.formState.isSubmitting}>
                Sign In
              </GlassButton>
            </form>
          )}

          {/* Register form */}
          {mode === 'register' && (
            <form onSubmit={registerForm.handleSubmit(handleRegister)} noValidate>
              <GlassField
                label="Username"
                htmlFor="reg-username"
                error={registerForm.formState.errors.username?.message}
              >
                <GlassInput
                  {...registerForm.register('username')}
                  id="reg-username"
                  type="text"
                  placeholder="johndoe"
                  autoComplete="username"
                  hasError={!!registerForm.formState.errors.username}
                />
              </GlassField>
              <GlassField
                label="Email"
                htmlFor="reg-email"
                error={registerForm.formState.errors.email?.message}
              >
                <GlassInput
                  {...registerForm.register('email')}
                  id="reg-email"
                  type="email"
                  placeholder="you@company.com"
                  autoComplete="email"
                  hasError={!!registerForm.formState.errors.email}
                />
              </GlassField>
              <GlassField
                label="Password"
                htmlFor="reg-password"
                error={registerForm.formState.errors.password?.message}
              >
                <GlassInput
                  {...registerForm.register('password')}
                  id="reg-password"
                  type="password"
                  placeholder="••••••••"
                  autoComplete="new-password"
                  hasError={!!registerForm.formState.errors.password}
                />
              </GlassField>
              <GlassField
                label="Confirm Password"
                htmlFor="reg-confirm"
                error={registerForm.formState.errors.confirmPassword?.message}
              >
                <GlassInput
                  {...registerForm.register('confirmPassword')}
                  id="reg-confirm"
                  type="password"
                  placeholder="••••••••"
                  autoComplete="new-password"
                  hasError={!!registerForm.formState.errors.confirmPassword}
                />
              </GlassField>
              <GlassButton loading={registerForm.formState.isSubmitting}>
                Create Account
              </GlassButton>
            </form>
          )}
        </div>
      </div>
    </div>
  )
}
