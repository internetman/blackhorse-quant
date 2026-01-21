'use client';
// 注意：前端引擎已废弃，数据更新现在由后端 FastAPI 引擎处理
// 此文件保留用于向后兼容，但不再使用

// 导出空函数以保持兼容性
export function startEngine() {
  // 数据更新由后端处理，前端不再需要本地引擎
  console.log('前端引擎已废弃，数据更新由后端处理');
}

export function stopEngine() {
  // 无需操作
}

export function setupStatusListener() {
  // 返回空的取消订阅函数
  return () => {};
}
