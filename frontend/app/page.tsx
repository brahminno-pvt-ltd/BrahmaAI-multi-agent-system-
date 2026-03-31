'use client'
import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/auth'

export default function Home() {
  const router = useRouter()
  const { user, isLoading } = useAuth()
  useEffect(() => {
    if (!isLoading) {
      router.replace(user ? '/chat' : '/login')
    }
  }, [user, isLoading, router])
  return null
}
