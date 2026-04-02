/**
 * Format date to readable string
 */
export function formatDate(date, format = 'YYYY-MM-DD HH:mm:ss') {
  if (!date) return '-'
  
  const d = new Date(date)
  if (isNaN(d.getTime())) return '-'

  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hours = String(d.getHours()).padStart(2, '0')
  const minutes = String(d.getMinutes()).padStart(2, '0')
  const seconds = String(d.getSeconds()).padStart(2, '0')

  return format
    .replace('YYYY', year)
    .replace('MM', month)
    .replace('DD', day)
    .replace('HH', hours)
    .replace('mm', minutes)
    .replace('ss', seconds)
}

/**
 * Format date time (alias for formatDate)
 */
export function formatDateTime(date, format = 'YYYY-MM-DD HH:mm:ss') {
  return formatDate(date, format)
}

/**
 * Format file size
 */
export function formatFileSize(bytes) {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

/**
 * Format percentage
 */
export function formatPercentage(value, decimals = 2) {
  if (value === null || value === undefined) return '-'
  return `${Number(value).toFixed(decimals)}%`
}

/**
 * Format IP address status
 */
export function formatIPStatus(status) {
  const statusMap = {
    available: '空闲',
    used: '已用',
    reserved: '保留'
  }
  return statusMap[status] || status
}

/**
 * Get IP status tag type
 */
export function getIPStatusType(status) {
  const typeMap = {
    available: 'success',
    used: 'warning',
    reserved: 'info'
  }
  return typeMap[status] || 'info'
}

/**
 * Format device type
 */
export function formatDeviceType(type) {
  const typeMap = {
    server: '服务器',
    switch: '交换机',
    router: '路由器',
    terminal: '终端',
    other: '其他'
  }
  return typeMap[type] || type
}

/**
 * Format operation type
 */
export function formatOperationType(type) {
  const typeMap = {
    create: '创建',
    update: '更新',
    delete: '删除',
    allocate: '分配',
    release: '回收'
  }
  return typeMap[type] || type
}

/**
 * Format resource type
 */
export function formatResourceType(type) {
  const typeMap = {
    ip: 'IP地址',
    device: '设备',
    segment: '网段',
    user: '用户'
  }
  return typeMap[type] || type
}
