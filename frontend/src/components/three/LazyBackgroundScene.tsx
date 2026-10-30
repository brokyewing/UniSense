import { lazy, Suspense, type ComponentType } from 'react'

const BackgroundScene = lazy(() => import('./BackgroundScene'))

export default function LazyBackgroundScene(props: Record<string, unknown>) {
  return (
    <Suspense fallback={null}>
      <BackgroundScene {...props} />
    </Suspense>
  )
}