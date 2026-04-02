"""
Unit tests for IP Address Service
测试 IP 地址分配、回收、保留等业务逻辑

需求覆盖：
- 2.1: IP 地址分配验证
- 2.3: IP 地址回收
- 2.4: IP 地址状态管理
- 2.6: IP 保留功能
"""
import pytest
from datetime import datetime
from app.services.ip_service import IPService
from app.models.ip_address import IPAddress
from app.models.device import Device


class TestIPAllocation:
    """测试 IP 分配流程"""
    
    def test_allocate_new_ip_success(self, db_session, test_segment, test_device, test_user):
        """
        测试成功分配新 IP 地址
        需求 2.1: 验证 IP 属于已存在的网段
        """
        # 分配一个不存在的 IP
        success, message, ip_record = IPService.allocate_ip(
            db=db_session,
            ip_address_str="192.168.1.50",
            device_id=test_device.id,
            user_id=test_user.id,
            segment_id=test_segment.id,
            skip_conflict_check=True
        )
        
        # 验证分配成功
        assert success is True
        assert "successfully" in message
        assert ip_record is not None
        assert ip_record.ip_address == "192.168.1.50"
        assert ip_record.status == "used"
        assert ip_record.device_id == test_device.id
        assert ip_record.allocated_by == test_user.id
        assert ip_record.allocated_at is not None
    
    def test_allocate_existing_available_ip(self, db_session, test_available_ip, test_device, test_user):
        """
        测试分配已存在的可用 IP
        需求 2.1: IP 分配流程
        """
        success, message, ip_record = IPService.allocate_ip(
            db=db_session,
            ip_address_str=test_available_ip.ip_address,
            device_id=test_device.id,
            user_id=test_user.id,
            skip_conflict_check=True
        )
        
        # 验证分配成功
        assert success is True
        assert ip_record.id == test_available_ip.id
        assert ip_record.status == "used"
        assert ip_record.device_id == test_device.id
    
    def test_allocate_used_ip_fails(self, db_session, test_used_ip, test_user):
        """
        测试分配已使用的 IP 应该失败
        需求 2.1: 冲突检测
        """
        # 创建另一个设备
        another_device = Device(
            name="Another Device",
            mac_address="11:22:33:44:55:66",
            owner="Another Owner",
            created_by=test_user.id
        )
        db_session.add(another_device)
        db_session.commit()
        
        # 尝试分配已使用的 IP
        success, message, ip_record = IPService.allocate_ip(
            db=db_session,
            ip_address_str=test_used_ip.ip_address,
            device_id=another_device.id,
            user_id=test_user.id,
            skip_conflict_check=True
        )
        
        # 验证分配失败
        assert success is False
        assert "Cannot allocate IP" in message
        assert ip_record is None
    
    def test_allocate_reserved_ip_fails(self, db_session, test_reserved_ip, test_device, test_user):
        """
        测试分配保留的 IP 应该失败
        需求 2.6: 保留 IP 不能被自动分配
        """
        success, message, ip_record = IPService.allocate_ip(
            db=db_session,
            ip_address_str=test_reserved_ip.ip_address,
            device_id=test_device.id,
            user_id=test_user.id,
            skip_conflict_check=True
        )
        
        # 验证分配失败
        assert success is False
        assert "Cannot allocate IP" in message
        assert ip_record is None
    
    def test_allocate_invalid_ip_format(self, db_session, test_device, test_user):
        """
        测试无效 IP 格式应该失败
        需求 2.1: IP 地址格式验证
        """
        success, message, ip_record = IPService.allocate_ip(
            db=db_session,
            ip_address_str="999.999.999.999",
            device_id=test_device.id,
            user_id=test_user.id,
            skip_conflict_check=True
        )
        
        # 验证失败
        assert success is False
        assert "Invalid IP address format" in message
        assert ip_record is None
    
    def test_allocate_ip_not_in_segment(self, db_session, test_segment, test_device, test_user):
        """
        测试 IP 不属于指定网段应该失败
        需求 2.1: 验证 IP 属于已存在的网段
        """
        success, message, ip_record = IPService.allocate_ip(
            db=db_session,
            ip_address_str="10.0.0.1",  # 不属于 192.168.1.0/24
            device_id=test_device.id,
            user_id=test_user.id,
            segment_id=test_segment.id,
            skip_conflict_check=True
        )
        
        # 验证失败
        assert success is False
        assert "does not belong to segment" in message
        assert ip_record is None
    
    def test_allocate_device_not_found(self, db_session, test_segment, test_user):
        """
        测试设备不存在应该失败
        需求 2.1: 关联设备信息
        """
        success, message, ip_record = IPService.allocate_ip(
            db=db_session,
            ip_address_str="192.168.1.60",
            device_id=99999,  # 不存在的设备 ID
            user_id=test_user.id,
            segment_id=test_segment.id,
            skip_conflict_check=True
        )
        
        # 验证失败
        assert success is False
        assert "Device not found" in message
        assert ip_record is None


class TestIPRelease:
    """测试 IP 回收流程"""
    
    def test_release_used_ip_by_address(self, db_session, test_used_ip, test_user):
        """
        测试通过 IP 地址回收已使用的 IP
        需求 2.3: 将 IP 状态更改为"空闲"并解除设备关联
        """
        original_device_id = test_used_ip.device_id
        
        success, message, ip_record = IPService.release_ip(
            db=db_session,
            ip_address_str=test_used_ip.ip_address,
            user_id=test_user.id
        )
        
        # 验证回收成功
        assert success is True
        assert "successfully" in message
        assert ip_record is not None
        assert ip_record.status == "available"
        assert ip_record.device_id is None
        assert ip_record.allocated_by is None
        assert ip_record.allocated_at is None
        
        # 验证原设备 ID 被记录
        assert original_device_id is not None
    
    def test_release_used_ip_by_id(self, db_session, test_used_ip, test_user):
        """
        测试通过 IP ID 回收已使用的 IP
        需求 2.3: IP 回收逻辑
        """
        success, message, ip_record = IPService.release_ip(
            db=db_session,
            ip_id=test_used_ip.id,
            user_id=test_user.id
        )
        
        # 验证回收成功
        assert success is True
        assert ip_record.status == "available"
        assert ip_record.device_id is None
    
    def test_release_reserved_ip(self, db_session, test_reserved_ip, test_user):
        """
        测试回收保留的 IP
        需求 2.3: 回收不同状态的 IP
        """
        success, message, ip_record = IPService.release_ip(
            db=db_session,
            ip_address_str=test_reserved_ip.ip_address,
            user_id=test_user.id
        )
        
        # 验证回收成功
        assert success is True
        assert ip_record.status == "available"
    
    def test_release_available_ip_fails(self, db_session, test_available_ip, test_user):
        """
        测试回收已经可用的 IP 应该失败
        需求 2.3: 状态验证
        """
        success, message, ip_record = IPService.release_ip(
            db=db_session,
            ip_address_str=test_available_ip.ip_address,
            user_id=test_user.id
        )
        
        # 验证失败
        assert success is False
        assert "already available" in message
    
    def test_release_nonexistent_ip(self, db_session, test_user):
        """
        测试回收不存在的 IP 应该失败
        需求 2.3: 错误处理
        """
        success, message, ip_record = IPService.release_ip(
            db=db_session,
            ip_address_str="192.168.1.99",
            user_id=test_user.id
        )
        
        # 验证失败
        assert success is False
        assert "not found" in message
        assert ip_record is None
    
    def test_release_without_identifier(self, db_session, test_user):
        """
        测试没有提供 IP 地址或 ID 应该失败
        需求 2.3: 参数验证
        """
        success, message, ip_record = IPService.release_ip(
            db=db_session,
            user_id=test_user.id
        )
        
        # 验证失败
        assert success is False
        assert "must be provided" in message
        assert ip_record is None


class TestIPReserve:
    """测试 IP 保留功能"""
    
    def test_reserve_available_ip(self, db_session, test_available_ip, test_user):
        """
        测试保留可用的 IP
        需求 2.4, 2.6: 手动标记 IP 为保留状态
        """
        success, message, ip_record = IPService.reserve_ip(
            db=db_session,
            ip_address_str=test_available_ip.ip_address,
            reserve=True,
            user_id=test_user.id
        )
        
        # 验证保留成功
        assert success is True
        assert "reserved successfully" in message
        assert ip_record.status == "reserved"
    
    def test_reserve_used_ip_fails(self, db_session, test_used_ip, test_user):
        """
        测试保留已使用的 IP 应该失败
        需求 2.6: 不能保留已使用的 IP
        """
        success, message, ip_record = IPService.reserve_ip(
            db=db_session,
            ip_address_str=test_used_ip.ip_address,
            reserve=True,
            user_id=test_user.id
        )
        
        # 验证失败
        assert success is False
        assert "Cannot reserve IP address that is in use" in message
    
    def test_reserve_already_reserved_ip_fails(self, db_session, test_reserved_ip, test_user):
        """
        测试保留已经保留的 IP 应该失败
        需求 2.4: 状态验证
        """
        success, message, ip_record = IPService.reserve_ip(
            db=db_session,
            ip_address_str=test_reserved_ip.ip_address,
            reserve=True,
            user_id=test_user.id
        )
        
        # 验证失败
        assert success is False
        assert "already reserved" in message
    
    def test_unreserve_reserved_ip(self, db_session, test_reserved_ip, test_user):
        """
        测试取消保留已保留的 IP
        需求 2.4: 取消保留功能
        """
        success, message, ip_record = IPService.reserve_ip(
            db=db_session,
            ip_address_str=test_reserved_ip.ip_address,
            reserve=False,
            user_id=test_user.id
        )
        
        # 验证取消保留成功
        assert success is True
        assert "cancelled successfully" in message
        assert ip_record.status == "available"
    
    def test_unreserve_non_reserved_ip_fails(self, db_session, test_available_ip, test_user):
        """
        测试取消保留非保留状态的 IP 应该失败
        需求 2.4: 状态验证
        """
        success, message, ip_record = IPService.reserve_ip(
            db=db_session,
            ip_address_str=test_available_ip.ip_address,
            reserve=False,
            user_id=test_user.id
        )
        
        # 验证失败
        assert success is False
        assert "not reserved" in message
    
    def test_reserve_by_ip_id(self, db_session, test_available_ip, test_user):
        """
        测试通过 IP ID 保留
        需求 2.6: 支持多种标识方式
        """
        success, message, ip_record = IPService.reserve_ip(
            db=db_session,
            ip_id=test_available_ip.id,
            reserve=True,
            user_id=test_user.id
        )
        
        # 验证保留成功
        assert success is True
        assert ip_record.status == "reserved"
    
    def test_reserve_without_identifier(self, db_session, test_user):
        """
        测试没有提供 IP 地址或 ID 应该失败
        需求 2.6: 参数验证
        """
        success, message, ip_record = IPService.reserve_ip(
            db=db_session,
            reserve=True,
            user_id=test_user.id
        )
        
        # 验证失败
        assert success is False
        assert "must be provided" in message
        assert ip_record is None


class TestIPStateTransitions:
    """测试 IP 状态转换"""
    
    def test_state_transition_available_to_used(self, db_session, test_available_ip, test_device, test_user):
        """
        测试状态转换：available -> used
        需求 2.4: IP 地址状态转换
        """
        # 初始状态
        assert test_available_ip.status == "available"
        
        # 分配 IP
        success, message, ip_record = IPService.allocate_ip(
            db=db_session,
            ip_address_str=test_available_ip.ip_address,
            device_id=test_device.id,
            user_id=test_user.id,
            skip_conflict_check=True
        )
        
        # 验证状态转换
        assert success is True
        assert ip_record.status == "used"
    
    def test_state_transition_used_to_available(self, db_session, test_used_ip, test_user):
        """
        测试状态转换：used -> available
        需求 2.4: IP 地址状态转换
        """
        # 初始状态
        assert test_used_ip.status == "used"
        
        # 回收 IP
        success, message, ip_record = IPService.release_ip(
            db=db_session,
            ip_address_str=test_used_ip.ip_address,
            user_id=test_user.id
        )
        
        # 验证状态转换
        assert success is True
        assert ip_record.status == "available"
    
    def test_state_transition_available_to_reserved(self, db_session, test_available_ip, test_user):
        """
        测试状态转换：available -> reserved
        需求 2.4: IP 地址状态转换
        """
        # 初始状态
        assert test_available_ip.status == "available"
        
        # 保留 IP
        success, message, ip_record = IPService.reserve_ip(
            db=db_session,
            ip_address_str=test_available_ip.ip_address,
            reserve=True,
            user_id=test_user.id
        )
        
        # 验证状态转换
        assert success is True
        assert ip_record.status == "reserved"
    
    def test_state_transition_reserved_to_available(self, db_session, test_reserved_ip, test_user):
        """
        测试状态转换：reserved -> available
        需求 2.4: IP 地址状态转换
        """
        # 初始状态
        assert test_reserved_ip.status == "reserved"
        
        # 取消保留
        success, message, ip_record = IPService.reserve_ip(
            db=db_session,
            ip_address_str=test_reserved_ip.ip_address,
            reserve=False,
            user_id=test_user.id
        )
        
        # 验证状态转换
        assert success is True
        assert ip_record.status == "available"
    
    def test_state_transition_reserved_to_available_via_release(self, db_session, test_reserved_ip, test_user):
        """
        测试状态转换：reserved -> available (通过 release)
        需求 2.4: IP 地址状态转换
        """
        # 初始状态
        assert test_reserved_ip.status == "reserved"
        
        # 回收保留的 IP
        success, message, ip_record = IPService.release_ip(
            db=db_session,
            ip_address_str=test_reserved_ip.ip_address,
            user_id=test_user.id
        )
        
        # 验证状态转换
        assert success is True
        assert ip_record.status == "available"
    
    def test_complete_lifecycle(self, db_session, test_segment, test_device, test_user):
        """
        测试完整的 IP 生命周期
        需求 2.1, 2.3, 2.4, 2.6: 完整的状态转换流程
        """
        ip_address = "192.168.1.100"
        
        # 1. 分配新 IP (不存在 -> used)
        success, _, ip_record = IPService.allocate_ip(
            db=db_session,
            ip_address_str=ip_address,
            device_id=test_device.id,
            user_id=test_user.id,
            segment_id=test_segment.id,
            skip_conflict_check=True
        )
        assert success is True
        assert ip_record.status == "used"
        
        # 2. 回收 IP (used -> available)
        success, _, ip_record = IPService.release_ip(
            db=db_session,
            ip_address_str=ip_address,
            user_id=test_user.id
        )
        assert success is True
        assert ip_record.status == "available"
        
        # 3. 保留 IP (available -> reserved)
        success, _, ip_record = IPService.reserve_ip(
            db=db_session,
            ip_address_str=ip_address,
            reserve=True,
            user_id=test_user.id
        )
        assert success is True
        assert ip_record.status == "reserved"
        
        # 4. 取消保留 (reserved -> available)
        success, _, ip_record = IPService.reserve_ip(
            db=db_session,
            ip_address_str=ip_address,
            reserve=False,
            user_id=test_user.id
        )
        assert success is True
        assert ip_record.status == "available"
        
        # 5. 再次分配 (available -> used)
        success, _, ip_record = IPService.allocate_ip(
            db=db_session,
            ip_address_str=ip_address,
            device_id=test_device.id,
            user_id=test_user.id,
            skip_conflict_check=True
        )
        assert success is True
        assert ip_record.status == "used"
