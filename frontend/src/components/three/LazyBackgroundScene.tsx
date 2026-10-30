import { lazy, Suspense } from 'react'

const BackgroundScene = lazy(() => import('./BackgroundScene'))

export default function LazyBackgroundScene(props) {
  return (
    <Suspense fallback={null}>
      <BackgroundScene {...props} />
    </Suspense>
  )
}