import request from './request'

/**
 * 获取设备列表
 */
export function getDevices(params) {
  return request({
    url: '/devices',
    method: 'get',
    params
  })
}

/**
 * 获取设备详情
 */
export function getDevice(id) {
  return request({
    url: `/devices/${id}`,
    method: 'get'
  })
}

/**
 * 创建设备
 */
export function createDevice(data) {
  return request({
    url: '/devices',
    method: 'post',
    data
  })
}

/**
 * 更新设备
 */
export function updateDevice(id, data) {
  return request({
    url: `/devices/${id}`,
    method: 'put',
    data
  })
}

/**
 * 删除设备
 */
export function deleteDevice(id) {
  return request({
    url: `/devices/${id}`,
    method: 'delete'
  })
}

/**
 * 获取设备关联的 IP 地址
 */
export function getDeviceIPs(id) {
  return request({
    url: `/devices/${id}/ips`,
    method: 'get'
  })
}
