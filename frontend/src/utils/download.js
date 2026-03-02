import api from '../api/client'

export async function downloadFile(url, filename) {
  const response = await api.get(url, { responseType: 'blob' })
  const blob = new Blob([response.data], { type: response.headers['content-type'] })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(link.href)
}
